from django.contrib.auth.backends import ModelBackend
from .models import User, AdminUser

class CustomAuthBackend(ModelBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        # Try AdminUser first (username-based)
        try:
            admin_user = AdminUser.objects.get(username=username)
            if admin_user.check_password(password):
                return admin_user
        except AdminUser.DoesNotExist:
            pass

        # Then try User (email-based)
        try:
            user = User.objects.get(email=username)
            if user.check_password(password):
                return user
        except User.DoesNotExist:
            return None
        
    def get_user(self, user_id):
        # Check both models by ID
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            try:
                return AdminUser.objects.get(pk=user_id)
            except AdminUser.DoesNotExist:
                return None