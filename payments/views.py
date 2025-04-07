import paypalrestsdk
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
import stripe
from .models import Donation, Payout
from emotes.services import roll_emote
from decimal import Decimal
from users.models import User
from emotes.models import Emote

# Configure PayPal
paypalrestsdk.configure({
    "mode": settings.PAYPAL_MODE,
    "client_id": settings.PAYPAL_CLIENT_ID,
    "client_secret": settings.PAYPAL_SECRET
})

# Configure Stripe
stripe.api_key = settings.STRIPE_SECRET_KEY

@csrf_exempt
@require_POST
@login_required
def donate(request):
    try:
        donor = request.user
        streamer_id = request.POST.get('streamer_id')
        amount = Decimal(request.POST.get('amount'))
        payment_method = request.POST.get('payment_method')
        payment_token = request.POST.get('payment_token')

        if not all([streamer_id, amount, payment_method, payment_token]):
            return JsonResponse({'error': 'Missing required fields'}, status=400)
        
        streamer = User.objects.get(id=streamer_id)
        if streamer == donor:
            return JsonResponse({'error': 'Cannot donate to yourself'}, status=400)
        
        # Calculate transaction fee (simplified; adjust based on actual rates)
        fee_rate = Decimal('0.029') # 2.9% typical for PayPal/Stripe
        fixed_fee = Decimal('0.30') # %0.30 fixed fee
        transaction_fee = (amount * fee_rate) + fixed_fee
        total_charge = amount + transaction_fee

        # Process payment
        if payment_method == 'paypal':
            payment = paypalrestsdk.Payment({
                "intent": "sale",
                "payer": {"payment_method": "paypal"},
                "transactions": [{
                    "amount": {
                        "total": f"{total_charge:.2f}",
                        "currency": "USD",
                        "details": {"subtotal": f"{amount:.2f}", "fee": f"{transaction_fee:.2f}"}
                    },
                    "description": f"Donation to {streamer.username}"
                }],
                "redirect_urls": {
                    "return_url": "http://localhost:8000/payments/success/",
                    "cancel_url": "http://localhost:8000/payments/cancel/"
                }
            })
            if payment.create():
                donation = Donation.objects.create(
                    donor=donor,
                    streamer=streamer,
                    amount=amount,
                    transaction_fee=transaction_fee,
                    payment_method='paypal',
                    payment_id=payment.id,
                    status='pending'
                )
                # In practice, redirect to payment['links'][1]['href'] for approval
                # For now, simulate success
                payment.execute({"payer_id": "dummy_payer_id"})
                donation.status = 'completed'
                donation.save()
            else:
                return JsonResponse({'error': payment.error}, status=400)
            
        elif payment_method == 'stripe':
            charge = stripe.Charge.create(
                amount=int(total_charge * 100), # Convert to cents
                currency="usd",
                source=payment_token,
                description=f"Donation to {streamer.username}"
            )
            donation = Donation.objects.create(
                donor=donor,
                streamer=streamer,
                amount=amount,
                transaction_fee=transaction_fee,
                payment_method='stripe',
                payment_id=charge.id,
                status='completed' if charge.status == 'succeeded' else 'failed'
            )
            if charge.status != 'succeeded':
                return JsonResponse({'error': 'Payment failed'}, status=400)
        
        # Unlock emotes (1 per $1)
        emote_count = int(amount) # Floor to nearest dollar
        unlocked_emotes = []
        for _ in range(emote_count):
            emote_name = roll_emote(donor)
            if emote_name:
                unlocked_emotes.append(emote_name)
        if unlocked_emotes:
            donation.emote_unlocked = Emote.objects.get(name=unlocked_emotes[0]) # Store first emote
            donation.save()

        # Update streamer balanace
        streamer_share, _ = donation.calculate_split()
        streamer.balance += streamer_share
        streamer.save()

        return JsonResponse({
            'message': 'Donation successful',
            'unlocked_emotes': unlocked_emotes,
            'donation_id': donation.id
        })
    
    except User.DoesNotExist:
        return JsonResponse({'error': 'Streamer not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
    
@login_required
@require_POST
def request_payout(request):
    try:
        user = request.user
        amount = Decimal(request.POST.get('amount'))
        method = request.POST.get('method') # 'paypal' or 'bank'

        if amount > user.balance:
            return JsonResponse({'error': 'Insufficient balance'}, status=400)
        if amount < Decimal('1.00'):
            return JsonResponse({'error': 'Minimum payout is $1.00'}, status=400)
        
        # Simulate payout (implement actual PayPal/Bank payout later)
        payout = Payout.objects.create(
            user=user,
            amount=amount,
            method=method,
            status='pending'
        )
        if method == 'paypal':
            # Placeholder for PayPal payout
            payout.payment_id = f"paypal_{payout.id}"
            payout.status = 'completed' # Simulate success
            payout.save()
        elif method == 'bank':
            # Placeholder for bank transfer (e.g., via Stripe or manual process)
            payout.payment_id = f"bank_{payout.id}"
            payout.status = 'completed' # Simulate success
            payout.save()

        user.balance -= amount
        user.save()

        return JsonResponse({'message': 'Payout requested', 'payout_id': payout.id})
    
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)