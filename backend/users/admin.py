from django.contrib import admin
from .models import User, AdminUser

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('email', 'twitch_id', 'username', 'display_name', 'date_created')

@admin.register(AdminUser)
class AdminUserAdmin(admin.ModelAdmin):
    list_display = ('username', 'is_staff', 'is_superuser', 'date_created')