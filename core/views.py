from django.contrib.auth.models import User
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from allauth.socialaccount.models import SocialAccount
import paypalrestsdk
from django.conf import settings
from django.urls import reverse
from .models import Donation, UserEmote
from django.contrib.auth import logout

paypalrestsdk.configure({
    "mode": "sandbox",
    "client_id": settings.PAYPAL_CLIENT_ID,
    "client_secret": settings.PAYPAL_SECRET
})

@login_required(login_url='/accounts/login/')
def dashboard(request):
    # Get Twitch social account data
    twitch_account = request.user.socialaccount_set.filter(provider='twitch').first()
    twitch_data = twitch_account.extra_data if twitch_account else {}
    username = twitch_data.get('display_name', request.user.username)
    donation_url = reverse('donate', args=[twitch_data.get('login', request.user.username)])
    user_emotes = UserEmote.objects.filter(user=request.user).select_related('emote_type')
    return render(request, 'dashboard.html', {
        'twitch_username': username,
        'twitch_email': twitch_data.get('email', 'N/A'),
        'twitch_id': twitch_data.get('id', 'N/A'),
        'donation_url': request.build_absolute_uri(donation_url),
        'user_emotes': user_emotes
    })

@login_required(login_url='/accounts/login/')
def donate(request, streamer_username):
    streamer = User.objects.get(socialaccount__extra_data__login=streamer_username)
    streamer_name = streamer.socialaccount_set.first().extra_data['display_name']
    if request.method == 'POST':
        amount = float(request.POST.get('amount', 0))
        processing_fee = (amount * 0.029) + 0.30
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
                'processing_fee': processing_fee,
                'anonymous': request.POST.get('anonymous', 'off') == 'on'
            }
            return redirect(next((link.href for link in payment.links if link.rel == "approval_url"), None))
        return render(request, 'payment_error.html', {'error': payment.error})
    return render(request, 'donate.html', {'streamer_name': streamer_name})

@login_required(login_url='/accounts/login/')
def payment_execute(request):
    payment_id = request.GET.get('paymentId')
    payer_id = request.GET.get('PayerID')
    payment = paypalrestsdk.Payment.find(payment_id)
    if payment.execute({"payer_id": payer_id}):
        donation_data = request.session.pop('donation', {})
        donor_twitch = request.user.socialaccount_set.first().extra_data['display_name']
        streamer = User.objects.get(id=donation_data['streamer_id'])
        donation = Donation.objects.create(
            user=request.user,
            streamer=streamer,
            amount=donation_data['amount'],
            payment_id=payment_id,
            anonymous=donation_data['anonymous']
        )
        total_paid = donation.amount + donation.processing_fee
        unlocked_emotes = donation.roll_for_emotes()
        return render(request, 'payment_success.html', {
            'donor_name': 'Anonymous' if donation.anonymous else donor_twitch,
            'streamer_name': streamer.socialaccount_set.first().extra_data['display_name'],
            'amount': donation.amount,
            'total_paid': total_paid,
            'net_to_streamer': donation.net_to_streamer,
            'emoterush_fee': donation.emoterush_fee,
            'unlocked_emotes': unlocked_emotes
        })
    return render(request, 'payment_error.html', {'error': payment.error})

@login_required(login_url='/accounts/login/')
def payment_cancel(request):
    return render(request, 'payment_cancel.html')

def custom_logout(request):
    if request.method == 'POST':
        # Only remove Twitch social account data, not full session
        if request.user.is_authenticated and request.user.socialaccount_set.exists():
            SocialAccount.objects.filter(user=request.user, provider='twitch').delete()
            logout(request)  # Full logout for now; refine later if needed
        return redirect('home')
    return render(request, 'account/logout.html', {'request': request})