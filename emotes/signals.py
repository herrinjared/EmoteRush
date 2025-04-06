from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Emote
from users.models import User

@receiver(post_save, sender=Emote)
def assign_new_emote_to_roles(sender, instance, created, **kwargs):
    """ Assign a new special emote to users with matching roles. """
    if created and instance.is_special():
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
                    emotes_dict[instance.name] = 1
                    user.set_emotes(emotes_dict)