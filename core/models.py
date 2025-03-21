from django.db import models
from django.contrib.auth.models import User
import random

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    twitch_id = models.CharField(max_length=50, unique=True, blank=True, null=True)

    def __str__(self):
        return f"{self.user.username}'s profile"

class EmoteType(models.Model):
    name = models.CharField(max_length=50, unique=True)
    image = models.FileField(upload_to='emotes/')
    rarity = models.CharField(max_length=20, choices=[
        ('common', 'Common'), ('uncommon', 'Uncommon'), ('rare', 'Rare'),
        ('epic', 'Epic'), ('legendary', 'Legendary'), ('mythic', 'Mythic')
    ])
    animated = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    available_instances = models.PositiveIntegerField()  # Total available

    class Meta:
        verbose_name = 'Emote Type'
        verbose_name_plural = 'Emote Types'

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.pk:  # Set initial availability on creation
            rarity_limits = {
                'common': 10000000, 'uncommon': 1000000, 'rare': 100000,
                'epic': 10000, 'legendary': 1000, 'mythic': 100
            }
            self.available_instances = rarity_limits.get(self.rarity, 1000000)
        super().save(*args, **kwargs)

class UserEmote(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='emotes')
    emote_type = models.ForeignKey(EmoteType, on_delete=models.CASCADE)
    count = models.PositiveIntegerField(default=1)  # Number owned by user
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'User Emote'
        verbose_name_plural = 'User Emotes'
        unique_together = ('user', 'emote_type')

    def __str__(self):
        return f"{self.user.username} - {self.emote_type.name} ({self.count})"

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
        chances = int(self.amount)
        unlocked_emotes = []
        rarities = [
            ('common', 0.50), ('uncommon', 0.30), ('rare', 0.15),
            ('epic', 0.04), ('legendary', 0.009), ('mythic', 0.001)
        ]
        for _ in range(chances):
            if random.random() < 0.5:
                rarity = random.choices(
                    [r[0] for r in rarities],
                    weights=[r[1] for r in rarities],
                    k=1
                )[0]
                emote_type = EmoteType.objects.filter(
                    rarity=rarity, available_instances__gt=0
                ).order_by('?').first()
                if emote_type:
                    user_emote, created = UserEmote.objects.get_or_create(
                        user=self.user,
                        emote_type=emote_type,
                        defaults={'count': 1}
                    )
                    if created:
                        emote_type.available_instances -= 1
                        emote_type.save()
                    else:
                        user_emote.count += 1
                        user_emote.save()
                    unlocked_emotes.append(user_emote)
        return unlocked_emotes

    def __str__(self):
        return f"{self.user.username} donated ${self.amount} to {self.streamer.username}"