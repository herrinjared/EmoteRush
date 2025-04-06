from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import User
from emotes.models import Emote

@receiver(post_save, sender=User)
def assign_existing_emotes(sender, instance, created, **kwargs):
    """ Assign existing special emotes to a new user based on eligibility. """
    if not created:
        return # Only trigger on user creation
    
    emotes_dict = instance.get_emotes()

    # Assign all pity emotes
    pity_emotes = Emote.objects.filter(rarity='pity')
    for emote in pity_emotes:
        if emote.name not in emotes_dict or emotes_dict[emote.name] < 1:
            if instance.allocate_instance():
                emotes_dict[emote.name] = 1

    # Assign earlydays emotes if user is in first 100
    early_users = User.objects.order_by('date_created')[:100]
    early_user_id = {user.id for user in early_users}
    if instance.id in early_user_id:
        earlydays_emotes = Emote.objects.filter(rarity='earlydays')
        for emote in earlydays_emotes:
            if emote.name not in emotes_dict or emotes_dict[emote.name] < 1:
                if instance.allocate_instance():
                    emotes_dict[emote.name] = 1

    # Assign role-based emotes (artist, developer, founder)
    role_field_map = {
        'is_artist': 'artist',
        'is_developer': 'developer',
        'is_founder': 'founder',
    }
    for role_field, rarity in role_field_map.items():
        if getattr(instance, role_field):
            role_emotes = Emote.objects.filter(rarity=rarity)
            for emote in role_emotes:
                if emote.name not in emotes_dict or emotes_dict[emote.name] < 1:
                    if instance.allocate_instance():
                        emotes_dict[emote.name] = 1

    # Save updated emotes
    if emotes_dict != instance.get_emotes(): # Only save if changed
        instance.set_emotes(emotes_dict)