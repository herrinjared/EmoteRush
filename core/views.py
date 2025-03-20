from django.contrib.auth.models import User
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from allauth.socialaccount.models import SocialAccount
import paypalrestsdk
from django.conf import settings
from django.urls import reverse

# Configure PayPal SDK
paypalrestsdk.configure({
    "mode": "sandbox",
    "client_id": settings.PAYPAL_CLIENT_ID,
    "client_secret": settings.PAYPAL_SECRET
})

@login_required
def dashboard(request):
    twitch_account = SocialAccount.objects.filter(user=request.user, provider='twitch').first()
    twitch_data = twitch_account.extra_data if twitch_account else {}
    username = twitch_data.get('display_name', 'Guest')
    donation_url = reverse('donate', args=[twitch_data.get('login', 'unknown')])
    return render(request, 'dashboard.html', {
        'twitch_username': username,
        'twitch_data': twitch_data,
        'donation_url': request.build_absolute_uri(donation_url)
    })

@login_required
def donate(request, streamer_username):
    streamer = User.objects.get(socialaccount__extra_data__login=streamer_username)
    streamer_name = streamer.socialaccount_set.first().extra_data['display_name']
    if request.method == 'POST':
        amount = float(request.POST.get('amount', 0))
        processing_fee = (amount * 0.029) + 0.30  # PayPal fee
        total_charge = amount + processing_fee
        payment = paypalrestsdk.Payment({
            "intent": "sale",
            "payer": {"payment_method": "paypal"},
            "redirect_urls": {
                "return_url": request.build_absolute_uri(reverse('payment_execute')),
                "cancel_url": request.build_absolute_uri(reverse('payment_cancel'))
            },
            "transactions": [{
                "amount": {"total": f"{total_charge:.2f}", "currency": "USD"},
                "description": f"Donation to {streamer_name}"
            }]
        })
        if payment.create():
            request.session['donation'] = {
                'streamer_id': streamer.id,
                'amount': amount,
                'anonymous': request.POST.get('anonymous', 'off') == 'on'
            }
            return redirect(next((link.href for link in payment.links if link.rel == "approval_url"), None))
        return render(request, 'payment_error.html', {'error': payment.error})
    return render(request, 'donate.html', {'streamer_name': streamer_name})

@login_required
def payment_execute(request):
    payment_id = request.GET.get('paymentId')
    payer_id = request.GET.get('PayerID')
    payment = paypalrestsdk.Payment.find(payment_id)
    if payment.execute({"payer_id": payer_id}):
        donation_data = request.session.pop('donation', {})
        # Save donation (Step 6.3 will add this)
        return render(request, 'payment_success.html', {'amount': donation_data['amount']})
    return render(request, 'payment_error.html', {'error': payment.error})

@login_required
def payment_cancel(request):
    return render(request, 'payment_cancel.html')