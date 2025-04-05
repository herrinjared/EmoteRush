from django.contrib import admin
from django import forms
import json
from .models import User, AdminUser
from emotes.models import Emote

class UserEmoteForm(forms.ModelForm):
    emotes = forms.CharField(
        widget=forms.Textarea,
        help_text="Edit as JSON, e.g., {'pity1': 1, 'common1': 3}. Special emotes limited to 1 unless forced."
    )

    class Meta:
        model = User
        fields = '__all__'

    def clean_emotes(self):
        emotes_str = self.cleande_data['emotes']
        try:
            emotes_dict = json.loads(emotes_str)
            for emote_name, count in emotes_dict.items():
                emote = Emote.objects.get(name=emote_name)
                if emote.is_special() and count > 1 and not self.user.is_superuser:
                    raise forms.ValidationError(f"Special emote '{emote_name}' cannot exceed 1 instance unless set by superuser.")
            return emotes_str
        except json.JSONDecodeError:
            raise forms.ValidationError("Invalid JSON format.")
        except Emote.DoesNotExist:
            raise forms.ValidationError(f"Emote '{emote_name}' does not exist.")

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('username', 'display_name', 'email', 'twitch_id', 'is_staff', 'is_superuser')
    list_filter = ('is_staff', 'is_superuser')
    search_fields = ('username', 'display_name' 'email', 'twitch_id')
    readonly_fields = ('twitch_id', 'changes_log', 'date_joined', 'last_login')
    fieldsets = (
        (None, {'fields': ('username', 'display_name', 'email', 'twitch_id')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser')}),
        ('Emotes', {'fields': ('emotes',)}),
        ('Logs', {'fields': ('changes_log',)}),
        ('Dates', {'fields': ('date_joined', 'last_login')}),
    )

@admin.register(AdminUser)
class AdminUserAdmin(admin.ModelAdmin):
    list_display = ('username', 'is_staff', 'is_superuser')
    list_filter = ('is_staff', 'is_superuser')
    search_fields = ('username',)
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser')}),
    )