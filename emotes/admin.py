from django.contrib import admin
from .models import Emote

class EmoteAdmin(admin.ModelAdmin):
    list_display = ('name', 'rarity', 'roll_chance', 'max_instances', 'created_at')
    list_filter = ('rarity',)
    search_fields = ('name',)
    fieldsets = (
        (None, {'fields': ('name', 'image')}),
        ('Properties', {'fields': ('rarity', 'roll_chance', 'max_instances')}),
    )

    def has_add_permission(self, request):
        if not request.user.is_superuser and self.rarity in ('pity', 'earlydays', 'devgod', 'artist', 'founder'):
            return False
        return True
    
    def get_readonly_fields(self, request, obj=None):
        if obj and obj.is_special():
            return ('rarity, max_instances') + self.readonly_fields
        return self.readonly_fields

admin.site.register(Emote, EmoteAdmin)