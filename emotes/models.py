from django.db import models, transaction
from django.core.exceptions import ValidationError
from PIL import Image
import os

def validate_square_image(image):
    """ Ensure image is square. """
    img = Image.open(image)
    if img.size[0] != img.size[1]:
        raise ValidationError("Emote image must square (width = height).")
    
def validate_emote_format_and_size(image, is_thumbnail=False):
    """ Validate format, dimensions, file size, transparency, and frames. """
    img = Image.open(image)
    width, height = img.size
    file_size = image.size / 1024 # Size in KB
    ext = os.path.splitext(image.name)[1].lower()

    # Format check
    if is_thumbnail:
        if ext != '.png':
            raise ValidationError("Thumbnail must be a PNG.")
    else:
        expected_ext = '.gif' if img.is_animated else '.png'
        if ext != expected_ext:
            raise ValidationError(f"Image must be {expected_ext[1:].upper()} (PNG for still, GIF for animated).")
        
    # Transparency for PNG
    if ext == '.png' and img.mode not in ('RGBA', 'LA'):
        raise ValidationError("PNG must have a transparent background (RGBA or LA mode).")
    
    # GIF from count
    if ext== '.gif' and img.is_animated and img.n_frames > 60:
        raise ValidationError("GIF cannot exceed 60 frames.")
    
    # Size and file limits
    if not (112 <= width <= 4096 and 112 <= height <= 4096):
        raise ValidationError("Image must be between 112x122px and 4096x4096px.")
    if file_size > 1024: # 1MB
        raise ValidationError("File size cannot exceed 1MB.")
    
def validate_thumbnail(image):
    """ Wrapper for thumbnail validation. """
    validate_emote_format_and_size(image, is_thumbnail=True)

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

    from django.contrib.auth import get_user_model
    User = get_user_model()

    name = models.CharField(max_length=47, help_text="User-friendly name without 'ER:' prefix (e.g., pity1)")
    chat_display_name = models.CharField(max_length=50, unique=True, help_text="Unique emote name with 'ER:' (e.g., ER:emote)", editable=False)
    rarity = models.CharField(max_length=20, choices=RARITY_CHOICES, default='common')
    image = models.ImageField(
        upload_to='emotes/',
        validators=[validate_square_image, validate_emote_format_and_size],
        help_text="PNG (still) or GIF (animated), 112x112px to 4096x4096px, ≤ 1MB. PNGs must be transparent, GIFs no more than 60 frames."
    )
    thumbnail = models.ImageField(
        upload_to='emotes/thumbs/',
        blank=True, null=True,
        validators=[validate_square_image, validate_thumbnail],
        help_text="Optional PNG thumbnail for GIFs (112x112px to 4096x4096px, ≤ 1MB). Defaults to first GIF frame."
    )
    artist = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_emotes',
        help_text="The user credited as the artist. Defaults to the creator unless set by an admin."
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
        # Set artist to the current user if not specified (for regular users)
        if not self.artist and hasattr(self, '_request_user') and not self._request_user.is_superuser:
            self.artist = self._request_user
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