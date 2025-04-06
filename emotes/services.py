import random
from .models import Emote
from django.contrib.auth import get_user_model

User = get_user_model()

RARITY_CHANCES = {
    'common': 70.0,
    'uncommon': 25.0,
    'rare': 5.0,
    'epic': 1.0,
    'legendary': 0.01,
    'exotic': 0.001,
    'mythic': 0.0001,
    'novelty': 0.00001,
}

RARITY_MAX_INSTANCES = {
    'common': 1000000000,
    'uncommon': 500000000,
    'rare': 100000000,
    'epic': 10000000,
    'legendary': 1000000,
    'exotic': 100000,
    'mythic': 10000,
    'novelty': 1,
}

def get_available_emotes():
    """ Return emotes with remaining instances, grouped by rarity. """
    available = {}
    all_users = User.objects.all()

    for emote in Emote.objects.exculde(rarity__in=['pity', 'earlydays', 'developer', 'artist', 'founder']):
        total_instances = sum(
            user.get_emotes().get(emote.name, 0) for user in all_users
        )
        max_instances = RARITY_MAX_INSTANCES.get(emote.rarity, 0)
        remaining = max_instances - total_instances

        if remaining > 0:
            if emote.rarity not in available:
                available[emote.rarity] = []
            available[emote.rarity].append((emote, remaining))

    return available

def roll_emote(user):
    """ Roll an emote from available eoptions based on hardcoded chances. """
    available_emotes = get_available_emotes()
    if not available_emotes:
        return None
    
    rollable_rarities = [r for r in RARITY_CHANCES.keys() if r in available_emotes]
    if not rollable_rarities:
        return None
    
    weights = [RARITY_CHANCES[r] for r in rollable_rarities]

    chosen_rarity = random.choices(rollable_rarities, weights=weights, k=1)[0]

    emotes, remaining_counts = zip(*available_emotes[chosen_rarity])
    chosen_emote = random.choices(emotes, weights=remaining_counts, k=1)[0]

    user.add_emote(chosen_emote.name)
    return chosen_emote.name