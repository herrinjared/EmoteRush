from django.contrib import admin
from django.utils.html import format_html
from .models import Emote

class EmoteAdmin(admin.ModelAdmin):
    list_display = ('name', 'chat_display_name', 'rarity', 'roll_chance', 'max_instances', 'created_at')
    list_filter = ('rarity',)
    search_fields = ('name', 'chat_display_name')
    fieldsets = (
        (None, {'fields': ('name', 'image')}),
        ('Properties', {'fields': ('rarity',)}),
        ('Read-Only', {'fields': ('chat_display_name', 'roll_chance', 'max_instances')}),
    )

    readonly_fields = ('chat_display_name', 'roll_chance', 'max_instances', 'created_at', 'updated_at')

    def formatted_roll_chance(self, obj):
        """ Display roll_chance as a percentage without decimals. """
        return f"{int(obj.roll_chance)}%" if obj.roll_chance.is_integer() else f"{obj.roll_chance}"
    formatted_roll_chance.short_description = 'Roll Chance'

    def formatted_max_instances(self, obj):
        """ Display max_instances with commas for readability. """
        return f"{obj.max_instances:,}" if obj.max_instances > 0 else "Unlimited"
    formatted_max_instances.short_description = "Max Instances"

    def has_add_permission(self, request):
        return request.user.is_superuser
    
    def get_readonly_fields(self, request, obj=None):
        fields = list(self.readonly_fields)
        if obj and obj.is_special() and not request.user.is_superuser:
            fields.extend(['rarity'])
        return fields
    
    def save_model(self, request, obj, form, change):
        # Ensure chat_display_name is set before saving
        obj.clean()
        super().save_model(request, obj, form, change)

admin.site.register(Emote, EmoteAdmin)