from django.db import models
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

    name = models.CharField(max_length=47, help_text="User-friendly name without 'ER:' prefix (e.g., pity1)")
    chat_display_name = models.CharField(max_length=50, unique=True, help_text="Unique emote name with 'ER:' (e.g., ER:emote)", editable=False)
    rarity = models.CharField(max_length=20, choices=RARITY_CHOICES, default='common')
    image = models.ImageField(
        upload_to='emotes/',
        blank=True, null=True,
        validators=[validate_square_image],
        help_text="Upload a square PNG or GIF (supports transparency and animation)."
    )
    roll_chance = models.FloatField(
        default=0.0,
        validators=[MinValueValidator(0.0), MaxValueValidator(100.0)],
        help_text="Chance of rolling this emote (0-100%), 0 for special emotes"
    )
    max_instances = models.BigIntegerField(
        default=0,
        help_text="Max instances allowed (0 for unlimited/special)"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def clean(self):
        # Auto-prefix chat_display_name
        proposed_chat_name = f"ER:{self.name}"
        if len(proposed_chat_name) > 50:
            raise ValidationError("Chat display name exceeds 50 characters with 'ER:' prefix.")
        self.chat_display_name = proposed_chat_name

    def save(self, *args, **kwargs):
        # Ensure chat_display_name is set before saving
        self.clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name} ({self.rarity})"
    
    def is_special(self):
        return self.rarity in ('pity', 'earlydays', 'developer', 'artist', 'founder')