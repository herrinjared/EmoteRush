from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from django.shortcuts import redirect
from .models import User
from django.db import IntegrityError
from emotes.models import Emote

class CustomSocialAccountAdapter(DefaultSocialAccountAdapter):
    def pre_social_login(self, request, sociallogin):
        user = sociallogin.user
        twitch_data = sociallogin.account.extra_data
        twitch_id = twitch_data.get('id')

        if request.user.is_authenticated:
            sociallogin.connect(request, request.user)
            user = request.user
        else:
            try:
                user = User.objects.get(twitch_id=twitch_id)
                sociallogin.connect(request, user)
            except User.DoesNotExist:
                user = sociallogin.user
                user.email = twitch_data.get('email', '')
                user.twitch_id = twitch_id
                user.username = twitch_data.get('login')
                user.twitch_channel_url = f"https://twitch.tv/{twitch_data.get('login')}"
                try:
                    user.save()
                    sociallogin.save(request)
                except IntegrityError:
                    user.username = f"{twitch_data.get('login')}_{twitch_id}"
                    user.save()
                    sociallogin.save(request)

        user.update_from_twitch(twitch_data)

    def authentication_error(self, request, provider_id, error, exception, extra_context):
        return redirect('/accounts/twitch/login/')