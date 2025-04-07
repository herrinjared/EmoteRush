from django.contrib import admin
from .models import Emote

class EmoteAdmin(admin.ModelAdmin):
    list_display = ('name', 'chat_display_name', 'rarity', 'artist', 'formatted_roll_chance', 'formatted_max_instances', 'remaining_instances', 'created_at')
    list_filter = ('rarity',)
    search_fields = ('name', 'chat_display_name')
    autocomplete_fields = ['artist']
    fieldsets = (
        (None, {'fields': ('name',)}),
        ('Image Upload', {
            'fields': ('image', 'thumbnail'),
            'description': (
                "Upload a PNG (still) or GIF (animated), 112x112px to 4096x4096px, ≤ 1MB.<br>"
                "PNGs must be transparent. GIFs must have no more than 60 frames.<br>"
                "Optional PNG thumbnail for GIFs (same rules); otherwise GIF thumbnail defaults to first frame."
            ),
        }),
        ('Properties', {'fields': ('rarity', 'artist')}),
        ('Read-Only', {
            'fields': ('chat_display_name', 'formatted_roll_chance', 'formatted_max_instances', 'remaining_instances'),
            'description': (
                "The Chat Display Name is set automatically based on the name you input above.<br>"
                "The Roll Chance and Max Instances values are set automatically based on the selected rarity.<br>"
                "Remaining emotes decrease as emotes are allocated."
            ),
        }),
    )
    readonly_fields = ('chat_display_name', 'formatted_roll_chance', 'formatted_max_instances', 'remaining_instances', 'created_at', 'updated_at')

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
        # Make artist readonly for non-superusers if already set
        if obj and not request.user.is_superuser:
            fields.append('artist')
        return fields
    
    def save_model(self, request, obj, form, change):
        # Pass the current user to the model for artist defaulting
        obj._request_user = request.user
        # Ensure chat_display_name is set before saving
        obj.clean()
        super().save_model(request, obj, form, change)

    class Media:
        js = ('admin/js/emote_rarity_update.js',)

admin.site.register(Emote, EmoteAdmin)