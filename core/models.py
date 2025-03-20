from django.db import models

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