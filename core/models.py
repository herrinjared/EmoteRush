from django.db import models
from django.contrib.auth.models import User
import random

class EmoteType(models.Model):
    name = models.CharField(max_length=50, unique=True)
    image = models.FileField(upload_to='emotes/')
    rarity = models.CharField(max_length=20, choices=[
        ('common', 'Common'), ('uncommon', 'Uncommon'), ('rare', 'Rare'),
        ('epic', 'Epic'), ('legendary', 'Legendary'), ('mythic', 'Mythic')
    ])
    animated = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Emote Type'
        verbose_name_plural = 'Emote Types'

    def __str__(self):
        return self.name

class UserEmote(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='emotes')
    emote_type = models.ForeignKey(EmoteType, on_delete=models.CASCADE)
    donation = models.ForeignKey('Donation', on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'User Emote'
        verbose_name_plural = 'User Emotes'

    def __str__(self):
        return f"{self.user.username} - {self.emote_type.name}"

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    twitch_id = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.user.username

class Donation(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='donations_made')
    streamer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='donations_received')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    emoterush_fee = models.DecimalField(max_digits=10, decimal_places=2)
    processing_fee = models.DecimalField(max_digits=10, decimal_places=2)
    net_to_streamer = models.DecimalField(max_digits=10, decimal_places=2)
    payment_id = models.CharField(max_length=255, unique=True)
    anonymous = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.pk:
            self.emoterush_fee = self.amount * 0.10
            self.processing_fee = (self.amount * 0.029) + 0.30
            self.net_to_streamer = self.amount * 0.90
        super().save(*args, **kwargs)

    def roll_for_emotes(self):
        """Roll for emotes: $1 = 50% chance."""
        chances = int(self.amount)  # $10 = 10 rolls
        unlocked_emotes = []
        rarities = [
            ('common', 0.50), ('uncommon', 0.30), ('rare', 0.15),
            ('epic', 0.04), ('legendary', 0.009), ('mythic', 0.001)
        ]
        for _ in range(chances):
            if random.random() < 0.5:  # 50% chance per dollar
                # Weighted random rarity
                rarity = random.choices(
                    [r[0] for r in rarities],
                    weights=[r[1] for r in rarities],
                    k=1
                )[0]
                emote_type = EmoteType.objects.filter(rarity=rarity).order_by('?').first()
                if emote_type:
                    user_emote = UserEmote.objects.create(
                        user=self.user,
                        emote_type=emote_type,
                        donation=self
                    )
                    unlocked_emotes.append(user_emote)
        return unlocked_emotes

    def __str__(self):
        return f"{self.user.username} donated ${self.amount} to {self.streamer.username}"