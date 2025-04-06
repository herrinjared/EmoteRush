from django.db import models, transaction
from django.core.validators import MinValueValidator, MaxValueValidator
from django.conf import settings
from PIL import Image
from django.core.exceptions import ValidationError

def validate_square_image(image):
    img = Image.open(image)
    width, height = img.size
    if width != height:
        raise ValidationError("Emote image must have a 1:1 aspect ratio (width = height).")

class Emote(models.Model):
    RARITY_CHOICES = (
        ('pity', 'Pity'),
        ('earlydays', 'EarlyDays'),
        ('developer', 'Developer'),
        ('artist', 'Artist'),
        ('founder', 'Founder'),
        ('common', 'Common'),
        ('uncommon', 'Uncommon'),
        ('rare', 'Rare'),
        ('epic', 'Epic'),
        ('legendary', 'Legendary'),
        ('exotic', 'Exotic'),
        ('mythic', 'Mythic'),
        ('novelty', 'Novelty'),
    )

    RARITY_CHANCES = {
        'pity': 0.0,
        'earlydays': 0.0,
        'developer': 0.0,
        'artist': 0.0,
        'founder': 0.0,
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
        'pity': 0,  # Unlimited for special
        'earlydays': 0,
        'developer': 0,
        'artist': 0,
        'founder': 0,
        'common': 1000000000,
        'uncommon': 500000000,
        'rare': 100000000,
        'epic': 10000000,
        'legendary': 1000000,
        'exotic': 100000,
        'mythic': 10000,
        'novelty': 1,
    }

    name = models.CharField(max_length=47, help_text="User-friendly name without 'ER:' prefix (e.g., pity1)")
    chat_display_name = models.CharField(max_length=50, unique=True, help_text="Unique emote name with 'ER:' (e.g., ER:emote)", editable=False)
    rarity = models.CharField(max_length=20, choices=RARITY_CHOICES, default='common')
    image = models.ImageField(
        upload_to='emotes/',
        blank=True, null=True,
        validators=[validate_square_image],
        help_text="Upload a square PNG or GIF (supports transparency and animation)."
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    remaining_instances = models.PositiveBigIntegerField(
        default=0,
        help_text="Number of instances still available. 0 means unlimited for special emotes."
    )

    def clean(self):
        # Auto-prefix chat_display_name
        proposed_chat_name = f"ER:{self.name}"
        if len(proposed_chat_name) > 50:
            raise ValidationError("Chat display name exceeds 50 characters with 'ER:' prefix.")
        self.chat_display_name = proposed_chat_name

    def save(self, *args, **kwargs):
        # Ensure chat_display_name is set before saving
        if self.pk is None:
            self.remaining_instances = self.max_instances
        self.clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name} ({self.rarity})"
    
    def is_special(self):
        return self.rarity in ('pity', 'earlydays', 'developer', 'artist', 'founder')
    
    @property
    def roll_chance(self):
        return self.RARITY_CHANCES.get(self.rarity, 0.0)
    
    @property
    def max_instances(self):
        return self.RARITY_MAX_INSTANCES.get(self.rarity, 0)
    
    @transaction.atomic
    def allocate_instance(self, count=1):
        """ Allocate instances and decrement remaining_instances. """
        if self.is_special() and self.remaining_instances == 0:
            return True
        if self.remaining_instances < count:
            return False
        self.remaining_instances -= count
        self.save(update_fields=['remaining_instances'])
        return True