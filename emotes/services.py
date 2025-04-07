import random
from .models import Emote
from django.contrib.auth import get_user_model

User = get_user_model()

def get_available_emotes():
    """ Return emotes with remaining instances, grouped by rarity. """
    available = {}
    for emote in Emote.objects.exclude(rarity__in=['pity', 'earlydays', 'developer', 'artist', 'founder']):
        if emote.remaining_instances > 0:
            if emote.rarity not in available:
                available[emote.rarity] = []
            available[emote.rarity].append((emote, emote.remaining_instances))
    return available

def roll_emote(user):
    """ Roll an emote from available eoptions based on hardcoded chances. """
    available_emotes = get_available_emotes()
    if not available_emotes:
        return None
    
    rollable_rarities = [r for r in Emote.RARITY_CHANCES.keys() if r in available_emotes]
    if not rollable_rarities:
        return None
    
    weights = [Emote.RARITY_CHANCES[r] for r in rollable_rarities]
    chosen_rarity = random.choices(rollable_rarities, weights=weights, k=1)[0]

    emotes, remaining_counts = zip(*available_emotes[chosen_rarity])
    chosen_emote = random.choices(emotes, weights=remaining_counts, k=1)[0]

    emotes_dict = user.get_emotes()
    old_count = emotes_dict.get(chosen_emote.name, 0)
    user.add_emote(chosen_emote.name)
    new_emotes_dict = user.get_emotes()
    if new_emotes_dict.get(chosen_emote.name, 0) > old_count:
        return chosen_emote.name
    return None