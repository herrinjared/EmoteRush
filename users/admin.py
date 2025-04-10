from django.contrib import admin
from django import forms
import json
from .models import User, AdminUser
from emotes.models import Emote

class UserEmoteForm(forms.ModelForm):
    emotes = forms.CharField(
        widget=forms.Textarea,
        help_text="Edit as JSON, e.g., {'pity1': 1, 'common1': 3}. Special emotes limited to 1 unless forced.",
        required=False
    )

    class Meta:
        model = User
        fields = '__all__'

    def clean_emotes(self):
        emotes_str = self.cleaned_data['emotes']
        if not emotes_str:
            return self.instance.emotes
        try:
            emotes_dict = json.loads(emotes_str)
            for emote_name, count in emotes_dict.items():
                emote = Emote.objects.get(name=emote_name)
                if emote.is_special() and count > 1:
                    raise forms.ValidationError(f"Special emote '{emote_name}' cannot exceed 1 instance unless set by superuser.")
            return emotes_str
        except json.JSONDecodeError:
            raise forms.ValidationError("Invalid JSON format.")
        except Emote.DoesNotExist:
            raise forms.ValidationError(f"Emote '{emote_name}' does not exist.")

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('username', 'display_name', 'email', 'twitch_id', 'balance_display', 'preferred_payout_method', 'agreed_to_terms', 'is_staff', 'is_superuser')
    list_filter = ('is_staff', 'is_superuser')
    search_fields = ('username', 'display_name', 'email', 'twitch_id')
    readonly_fields = ('twitch_id', 'balance_display', 'changes_log', 'date_joined', 'last_login')
    fieldsets = (
        (None, {'fields': ('username', 'display_name', 'email', 'twitch_id', 'paypal_email', 'stripe_account_id')}),
        ('Payout Preferences', {'fields': ('preferred_payout_method', 'agreed_to_terms')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser')}),
        ('Roles', {
            'fields': ('is_artist', 'is_developer', 'is_founder'),
            'description': "Check to assign all emotes of the corresponding rarity (e.g., Artist gets all 'artist' emotes).",
            'classes': ('collapse',)
        }),
        ('Emotes', {'fields': ('emotes',)}),
        ('Financials', {'fields': ('balance_display',)}),
        ('Logs', {'fields': ('changes_log',)}),
        ('Dates', {'fields': ('date_joined', 'last_login')}),
    )

    def balance_display(self, obj):
        return f"{obj.balance:.2f}"
    balance_display.short_description = "Balance"

    def save_model(self, request, obj, form, change):
        if not request.user.is_superuser:
            # Non-superusers can't edit roles
            obj.is_artist = obj._original_is_artist if hasattr(obj, '_original_is_artist') else False
            obj.is_developer = obj._original_is_developer if hasattr(obj, '_original_is_developer') else False
            obj.is_founder = obj._original_is_founder if hasattr(obj, '_original_is_founder') else False
        else:
            # Store original values for comparison
            if not change:
                obj._original_is_artist = False
                obj._original_is_developer = False
                obj._original_is_founder = False
            else:
                obj._original_is_artist = User.objects.get(pk=obj.pk).is_artist
                obj._original_is_developer = User.objects.get(pk=obj.pk).is_developer
                obj._original_is_founder = User.objects.get(pk=obj.pk).is_founder

            # Assign emotes if roles changed
            if obj.is_artist and not obj._original_is_artist:
                obj.assign_role_emotes('is_artist', 'artist')
            if obj.is_developer and not obj._original_is_developer:
                obj.assign_role_emotes('is_developer', 'developer')
            if obj.is_founder and not obj._original_is_founder:
                obj.assign_role_emotes('is_founder', 'founder')

        if request.user.is_superuser and form.cleaned_data['emotes']:
            obj.set_emotes(json.loads(form.cleaned_data['emotes']))
        elif form.cleaned_data['emotes']:
            emotes_dict = json.loads(form.cleaned_data['emotes'])
            for emote_name, count in emotes_dict.items():
                emote = Emote.objects.get(name=emote_name)
                if emote.is_special() and count > 1:
                    emotes_dict[emote_name] = 1
            obj.set_emotes(emotes_dict)

        super().save_model(request, obj, form, change)
    
    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        if not request.user.is_superuser:
            form.base_fields['is_artist'].disabled = True
            form.base_fields['is_developer'].disabled = True
            form.base_fields['is_founder'].disabled = True
        return form

@admin.register(AdminUser)
class AdminUserAdmin(admin.ModelAdmin):
    list_display = ('username', 'is_staff', 'is_superuser')
    list_filter = ('is_staff', 'is_superuser')
    search_fields = ('username',)
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser')}),
    )