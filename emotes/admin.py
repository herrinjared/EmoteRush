from django.contrib import admin
from .models import Emote

class EmoteAdmin(admin.ModelAdmin):
    list_display = ('name', 'chat_display_name', 'rarity', 'roll_chance', 'max_instances', 'created_at')
    list_filter = ('rarity',)
    search_fields = ('name', 'chat_display_name')
    fieldsets = (
        (None, {'fields': ('name', 'image')}),
        ('Properties', {'fields': ('rarity', 'roll_chance', 'max_instances')}),
        ('Read-Only', {'fields': ('chat_display_name',)}),
    )

    readonly_fields = ('chat_display_name', 'created_at', 'updated_at')

    def has_add_permission(self, request):
        return request.user.is_superuser
    
    def get_readonly_fields(self, request, obj=None):
        fields = list(self.readonly_fields)
        if obj and obj.is_special() and not request.user.is_superuser:
            fields.extend(['rarity', 'max_instances'])
        return fields
    
    def save_model(self, request, obj, form, change):
        # Ensure chat_display_name is set before saving
        obj.clean()
        super().save_model(request, obj, form, change)

admin.site.register(Emote, EmoteAdmin)