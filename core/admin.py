from django.contrib import admin
from .models import UserProfile, EmoteType, UserEmote, Donation

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'twitch_id')
    search_fields = ('user__username', 'twitch_id')

@admin.register(EmoteType)
class EmoteTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'rarity', 'available_instances', 'animated')
    list_filter = ('rarity', 'animated')
    search_fields = ('name',)

@admin.register(UserEmote)
class UserEmoteAdmin(admin.ModelAdmin):
    list_display = ('user', 'emote_type', 'count', 'created_at')
    list_filter = ('emote_type__rarity',)
    search_fields = ('user__username', 'emote_type__name')

@admin.register(Donation)
class DonationAdmin(admin.ModelAdmin):
    list_display = ('user', 'streamer', 'amount', 'net_to_streamer', 'created_at', 'anonymous')
    list_filter = ('anonymous', 'created_at')
    search_fields = ('user__username', 'streamer__username', 'payment_id')