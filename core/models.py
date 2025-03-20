from django.db import models
from django.contrib.auth.models import User
# Create your models here.
class Emote(models.Model):
    '''Model definition for Emote.'''
    
    name = models.CharField(max_length=50, unique=True)
    image = models.FileField(upload_to='emotes/')
    rarity = models.CharField(max_length=20, choices=[
        ('common', 'Common'), ('uncommon', 'Uncommon'), ('rare', 'Rare'),
        ('epic', 'Epic'), ('legendary', 'Legendary'), ('mythic', 'Mythic')
    ])
    animated = models.BooleanField(default=False)
    owner = models.ForeignKey('auth.User', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        '''Meta definition for Emote.'''

        verbose_name = 'Emote'
        verbose_name_plural = 'Emotes'

    def __str__(self):
        return self.name

class Profile(models.Model):
    '''Model definition for Profile.'''

    user = models.OneToOneField('auth.User', on_delete=models.CASCADE)
    twitch_id = models.CharField(max_length=50, unique=True)
    emotes = models.ManyToManyField(Emote, blank=True)

    class Meta:
        '''Meta definition for Profile.'''

        verbose_name = 'Profile'
        verbose_name_plural = 'Profiles'

    def __str__(self):
        return self.user.username

class Donation(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='donations_made')
    streamer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='donations_received')
    amount = models.DecimalField(max_digits=10, decimal_places=2)  # Base donation
    emoterush_fee = models.DecimalField(max_digits=10, decimal_places=2)  # $1 for $10
    processing_fee = models.DecimalField(max_digits=10, decimal_places=2)  # PayPal fee
    net_to_streamer = models.DecimalField(max_digits=10, decimal_places=2)  # $9 for $10
    payment_id = models.CharField(max_length=255, unique=True)
    anonymous = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.pk:  # Only on creation
            self.emoterush_fee = self.amount * 0.10  # 10% = $1 for $10
            self.processing_fee = (self.amount * 0.029) + 0.30  # PayPal fee on base
            self.net_to_streamer = self.amount * 0.90  # 90% = $9 for $10
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.user.username} donated ${self.amount} to {self.streamer.username}"