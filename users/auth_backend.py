from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model
from .models import AdminUser

class CustomAuthBackend(ModelBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        # Try AdminUser first (username-based)
        try:
            user = AdminUser.objects.get(username=username)
            if user.check_password(password):
                return user
        except AdminUser.DoesNotExist:
            UserModel = get_user_model()
            try:
                user = UserModel.objects.get(email=username)
                if user.check_password(password):
                    return user
            except UserModel.DoesNotExist:
                return None
        
    def get_user(self, user_id):
        try:
            return AdminUser.objects.get(pk=user_id)
        except AdminUser.DoesNotExist:
            UserModel = get_user_model()
            try:
                return UserModel.objects.get(pk=user_id)
            except UserModel.DoesNotExist:
                return None