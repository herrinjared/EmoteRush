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

    name = models.CharField(max_length=100, unique=True)
    image = models.ImageField(
        upload_to='emotes/',
        blank=True, null=True,
        validators=[validate_square_image],
        help_text="Upload a square PNG or GIF (supports transparency and animation)."
    )
    rarity = models.CharField(max_length=20, choices=RARITY_CHOICES, default='common')
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

    def __str__(self):
        return f"{self.name} ({self.rarity})"
    
    def is_special(self):
        return self.rarity in ('pity', 'earlydays', 'developer', 'artist', 'founder')