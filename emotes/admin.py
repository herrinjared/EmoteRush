from django.contrib import admin
from django.utils.html import format_html
from .models import Emote

class EmoteAdmin(admin.ModelAdmin):
    list_display = ('name', 'chat_display_name', 'rarity', 'formatted_roll_chance', 'formatted_max_instances', 'created_at')
    list_filter = ('rarity',)
    search_fields = ('name', 'chat_display_name')
    fieldsets = (
        (None, {'fields': ('name', 'image')}),
        ('Properties', {'fields': ('rarity',)}),
        ('Read-Only', {
            'fields': ('chat_display_name', 'formatted_roll_chance', 'formatted_max_instances'),
            'description': "These values update based on the selected rarity."
        }),
    )
    readonly_fields = ('chat_display_name', 'formatted_roll_chance', 'formatted_max_instances', 'created_at', 'updated_at')

    def formatted_roll_chance(self, obj):
        """ Display roll_chance as a percentage without decimals but with likelihood help text. """
        chance = obj.roll_chance
        if chance == 0:
            return "0% (Not rollable)"
        # Convert percentage to fraction (e.g., 70% = 0.7, 0.01% = 0.0001)
        fraction = chance / 100
        likelihood = 1 / fraction if fraction > 0 else float('inf')
        # Format likelihood
        if likelihood.is_integer():
            likelihood_text = f"1 in {int(likelihood):,}"
        elif likelihood < 100:
            likelihood_text = f"1 in {likelihood:.1f}"
        else:
            likelihood_text = f"1 in {int(likelihood):,}"
        return f"{int(chance)}%" if chance.is_integer() else f"{chance}% (about {likelihood_text})"
    formatted_roll_chance.short_description = 'Roll Chance'
    formatted_roll_chance.help_text = "Percentage chance of rolling this rarity, with approximate likelihood."

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

    class Media:
        js = ('admin/js/emote_rarity_update.js',)

admin.site.register(Emote, EmoteAdmin)