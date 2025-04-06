from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Emote
from users.models import User

@receiver(post_save, sender=Emote)
def assign_new_emote(sender, instance, created, **kwargs):
    """ Assign new emote to eligible users based on its rarity. """
    if not created:
        return # Only trigger on creation, not updates
    
    # Pre-fetch first 100 users for earlydays (shared across logic if needed)
    early_users = User.objects.order_by('date_created')[:100]
    early_user_ids = {user.id for user in early_users}

    # Assign pity emotes to all users
    if instance.rarity == 'pity':
        users = User.objects.all()
        for user in users:
            emotes_dict = user.get_emotes()
            if instance.name not in emotes_dict or emotes_dict[instance.name] < 1:
                if instance.allocate_instance():
                    emotes_dict[instance.name] = 1
                    user.set_emotes(emotes_dict)
    
    # Assign earlydays emotes to first 100 users
    if instance.rarity == 'earlydays':
        users = User.objects.filter(id__in=early_user_ids)  # Use pre-fetched IDs
        for user in users:
            emotes_dict = user.get_emotes()
            if instance.name not in emotes_dict or emotes_dict[instance.name] < 1:
                if instance.allocate_instance():
                    emotes_dict[instance.name] = 1
                    user.set_emotes(emotes_dict)
    
    # Assign role-based emotes (artist, developer, founder)
    role_field_map = {
        'artist': 'is_artist',
        'developer':'is_developer',
        'founder': 'is_founder',
    }
    role_field = role_field_map.get(instance.rarity)
    if role_field:
        users = User.objects.filter(**{role_field: True})
        for user in users:
            emotes_dict = user.get_emotes()
            if instance.name not in emotes_dict or emotes_dict[instance.name] < 1:
                if instance.allocate_instance():
                    emotes_dict[instance.name] = 1
                    user.set_emotes(emotes_dict)