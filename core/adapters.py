from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from django.contrib.auth.models import User
from core.models import UserProfile
from django.db import IntegrityError

class CustomSocialAccountAdapter(DefaultSocialAccountAdapter):
    def pre_social_login(self, request, sociallogin):
        """
        Hook before social login completes. Link or update user based on Twitch ID.
        """
        twitch_data = sociallogin.account.extra_data
        twitch_id = twitch_data.get('id')
        twitch_login = twitch_data.get('login')

        # If user is already logged in, link the Twitch account
        if request.user.is_authenticated:
            sociallogin.connect(request, request.user)
            return

        # Check if Twitch account already exists in socialaccount
        if sociallogin.is_existing:
            return  # Proceed with existing link

        # Check for user with matching twitch_id
        try:
            profile = UserProfile.objects.get(twitch_id=twitch_id)
            user = profile.user
            # Update username if it changed on Twitch
            if user.username != twitch_login:
                try:
                    user.username = twitch_login
                    user.save()
                except IntegrityError:
                    # If new username is taken, append twitch_id
                    user.username = f"{twitch_login}_{twitch_id}"
                    user.save()
            sociallogin.connect(request, user)
            return
        except UserProfile.DoesNotExist:
            pass  # No profile yet, proceed to create

        # New user: create with twitch_login as username
        user = sociallogin.user
        if not user.pk:
            user.username = twitch_login
            user.email = twitch_data.get('email', '')
            try:
                user.save()
                UserProfile.objects.create(user=user, twitch_id=twitch_id)
                sociallogin.save(request)
            except IntegrityError:
                # Handle rare case where username is taken
                user.username = f"{twitch_login}_{twitch_id}"
                user.save()
                UserProfile.objects.create(user=user, twitch_id=twitch_id)
                sociallogin.save(request)

    def populate_user(self, request, sociallogin, data):
        """
        Populate user fields from Twitch data.
        """
        user = super().populate_user(request, sociallogin, data)
        twitch_data = sociallogin.account.extra_data
        twitch_id = twitch_data.get('id')
        twitch_login = twitch_data.get('login')

        # Check if user exists by twitch_id
        try:
            profile = UserProfile.objects.get(twitch_id=twitch_id)
            user = profile.user
            if user.username != twitch_login:
                try:
                    user.username = twitch_login
                    user.save()
                except IntegrityError:
                    user.username = f"{twitch_login}_{twitch_id}"
                    user.save()
        except UserProfile.DoesNotExist:
            # Only set username if not already set
            if not user.username:
                user.username = twitch_login

        user.email = twitch_data.get('email', '')
        return user