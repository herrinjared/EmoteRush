from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from .models import Donation, Payout
from decimal import Decimal
import stripe

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

        streamer = donor.__class__.objects.get(id=streamer_id)
        if streamer == donor:
            return JsonResponse({'error': 'Cannot donate to yourself'}, status=400)

        donation = Donation(
            donor=donor,
            streamer=streamer,
            amount=Decimal(amount),
            payment_method=payment_method,
            payment_id="temp"
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

@login_required
@require_POST
def connect_paypal(request):
    try:
        paypal_email = request.POST.get('paypal_email')
        if not paypal_email:
            return JsonResponse({'error': 'PayPal email required'}, status=400)
        request.user.paypal_email = paypal_email
        request.user.save()
        return JsonResponse({'message': 'PayPal account connected'})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required
@require_POST
def connect_stripe(request):
    try:
        account = stripe.Account.create(
            type="express",
            email=request.user.email,
            capabilities={"transfers": {"requested": True}},
        )
        request.user.stripe_account_id = account.id
        request.user.save()
        account_link = stripe.AccountLink.create(
            account=account.id,
            refresh_url="http://localhost:8000/payments/refresh/",
            return_url="http://localhost:8000/payments/success/",
            type="account_onboarding",
        )
        return JsonResponse({'url': account_link.url})
    except stripe.error.StripeError as e:
        return JsonResponse({'error': f"Stripe error: {str(e)}"}, status=500)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required
@require_POST
def set_preferred_payout(request):
    try:
        method = request.POST.get('method')
        if method not in ['paypal', 'bank']:
            return JsonResponse({'error': 'Invalid method'}, status=400)
        if method == 'paypal' and not request.user.paypal_email:
            return JsonResponse({'error': 'Connect PayPal account first'}, status=400)
        if method == 'bank' and not request.user.stripe_account_id:
            return JsonResponse({'error': 'Connect bank account via Stripe first'}, status=400)
        request.user.preferred_payout_method = method
        request.user.save()
        return JsonResponse({'message': f"Preferred payout method set to {method}"})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required
@require_POST
def agree_to_terms(request):
    try:
        agreed = request.POST.get('agreed') == 'true'
        if not agreed:
            return JsonResponse({'error': 'You must agree to the terms'}, status=400)
        request.user.agreed_to_terms = True
        request.user.save()
        return JsonResponse({'message': 'Terms agreed'})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)