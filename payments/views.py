from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from .models import Donation, Payout
from decimal import Decimal
import stripe
from django.conf import settings

@csrf_exempt
@require_POST
@login_required
def donate(request):
    try:
        donor = request.user
        streamer_id = request.POST.get('streamer_id')
        amount = request.POST.get('amount')
        payment_method = request.POST.get('payment_method')
        payment_token = request.POST.get('payment_token')

        if not all([streamer_id, amount, payment_method, payment_token]):
            return JsonResponse({'error': 'Missing required fields'}, status=400)

        streamer = donor.__class__.objects.get(id=streamer_id)  # Use same model as donor
        if streamer == donor:
            return JsonResponse({'error': 'Cannot donate to yourself'}, status=400)

        donation = Donation(
            donor=donor,
            streamer=streamer,
            amount=Decimal(amount),
            payment_method=payment_method,
            payment_id="temp"  # Temporary, updated in process_payment
        )
        donation.process_payment(payment_token)
        unlocked_emotes = donation.unlock_emotes()
        donation.distribute_funds()

        return JsonResponse({
            'message': 'Donation successful',
            'unlocked_emotes': unlocked_emotes,
            'donation_id': donation.id
        })

    except donor.__class__.DoesNotExist:
        return JsonResponse({'error': 'Streamer not found'}, status=404)
    except ValueError as e:
        return JsonResponse({'error': str(e)}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required
@require_POST
def request_payout(request):
    try:
        user = request.user
        amount = request.POST.get('amount')
        method = request.POST.get('method')

        if not all([amount, method]):
            return JsonResponse({'error': 'Missing required fields'}, status=400)

        payout = Payout(user=user, amount=Decimal(amount), method=method)
        payout.process_payout()

        return JsonResponse({
            'message': 'Payout requested',
            'payout_id': payout.id,
            'net_amount': f"{payout.net_amount():.2f}",
            'fee': f"{payout.calculate_payout_fee():.2f}"
        })

    except ValueError as e:
        return JsonResponse({'error': str(e)}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
    
def create_stripe_account(request):
    if request.method == 'POST':
        account = stripe.Account.create(
            type='express',
            email=request.user.email,
            capabilities={"transfers": {"requested": True}},
        )
        request.user.stripe_account_id = account.id
        request.user.save()
        account_link = stripe.AccountLink.create(
            account=account.id,
            refresh_url='http://localhost:8000/refresh',
            return_url='http://localhost:8000/success',
            type='account_onboarding',
        )
        return JsonResponse({'url': account_link.url})