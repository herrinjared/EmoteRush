from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from allauth.socialaccount.models import SocialAccount

@login_required
def dashboard(request):
    twitch_account = SocialAccount.objects.filter(user=request.user, provider='twitch').first()
    twitch_data = twitch_account.extra_data if twitch_account else {}
    username = twitch_data.get('display_name', 'Guest') if twitch_account else 'Guest'
    return render(request, 'dashboard.html', {
        'user': request.user,
        'twitch_username': username,
        'twitch_data': twitch_data
    })