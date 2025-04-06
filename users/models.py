from django.db import models
from django.contrib.auth.models import AbstractUser, AbstractBaseUser, PermissionsMixin, BaseUserManager
from django.utils import timezone
import json
from emotes.models import Emote

class User(AbstractUser):
    # Core fields from Twitch
    email = models.EmailField(unique=True, blank=False, null=False, help_text="User's email from Twitch")
    twitch_id = models.CharField(max_length=25, unique=True, blank=False, null=False, help_text="Unique Twitch user ID")
    username = models.CharField(max_length=150, unique=True, blank=False, null=False, help_text="Username from Twitch")
    display_name = models.CharField(max_length=150, blank=True, null=True, help_text="Display name from Twitch")
    twitch_channel_url = models.URLField(blank=False, null=False, help_text="Twitch channel URL")

    # EmoteRush-specific fields
    emotes = models.TextField(default='{}', help_text="JSON of emote counts, e.g., {'pity1': 1, 'common1': 3}")     # JSON: {"ER:pity1": 1}
    balance = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)    # For payouts

    # Roll designations
    is_artist = models.BooleanField(default=False, help_text="User is an Artist, gets all artist emotes")
    is_developer = models.BooleanField(default=False, help_text="User is a Developer, gets all developer emotes")
    is_founder = models.BooleanField(default=False, help_text="User is a Founder, gets all founder emotes")

    # Timestamps and change log
    date_created = models.DateTimeField(default=timezone.now, help_text="When the user was created")
    date_updated = models.DateTimeField(auto_now=True, help_text="Last updated time")
    changes_log = models.TextField(blank=True, null=True, help_text="Log of changes to user data")

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['twitch_id']

    def get_emotes(self):
        return json.loads(self.emotes)
    
    def set_emotes(self, emotes_dict):
        self.emotes = json.dumps(emotes_dict)

    def add_emote(self, emote_name, count=1, force_special=False):
        """ Add an emote instance, respecting special emote limits unless forced. """
        emotes_dict = self.get_emotes()
        emote = Emote.objects.get(name=emote_name)

        current_count = emotes_dict.get(emote_name, 0)
        if emote.is_special() and current_count >=1 and not force_special:
            return # Not duplicates for special emotes unless forced
        emotes_dict[emote_name] = current_count + count
        self.set_emotes(emotes_dict)

    def assign_role_emotes(self, role_field, rarity):
        """ Assign all emotes of a given rarity if the role is enabled. """
        if getattr(self, role_field):
            emotes_dict = self.get_emotes()
            role_emotes = Emote.objects.filter(rarity=rarity)
            for emote in role_emotes:
                if emote.name not in emotes_dict or emotes_dict[emote.name] < 1:
                    emotes_dict[emote.name] = 1
            self.set_emotes(emotes_dict)

    def update_from_twitch(self, twitch_data):
        """
        Update user fields from Twitch API data and log changes.
        Args:
            twitch_data (dict): Data from Twitch API (e.g., {'id': '123', 'login': 'user', ...})
        """
        changed = False
        log_entries = []

        fields_to_update = {
            'twitch_id': twitch_data.get('id'),
            'email': twitch_data.get('email'),
            'display_name': twitch_data.get('display_name') or twitch_data.get('login'),
            'username': twitch_data.get('login'),
        }

        for field, new_value in fields_to_update.items():
            old_value = getattr(self, field)
            if old_value != new_value:
                log_entries.append(f"{field.capitalize()} changed: {old_value} -> {new_value}")
                setattr(self, field, new_value)
                changed = True

        new_channel_url = f"https://twitch.tv/{twitch_data.get('login')}"
        if self.twitch_channel_url != new_channel_url:
            self.twitch_channel_url = new_channel_url
            changed = True

        if changed:
            current_log = self.changes_log or ""
            timestamp = timezone.now().strftime("%d %B %Y %H:%M %Z")
            new_log = "\n".join([f"{timezone.now()}: {entry}" for entry in log_entries])
            self.changes_log = f"{current_log}\n{new_log}".strip()
            self.save()

    def __str__(self):
        return self.email or self.twitch_id
    
class AdminUserManager(BaseUserManager):
    def create_user(self, username, password=None, **extra_fields):
        if not username:
            raise ValueError("A username is required.")
        user = self.model(username=username, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user
    
    def create_superuser(self, username, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')
        return self.create_user(username, password, **extra_fields)
    
class AdminUser(AbstractBaseUser, PermissionsMixin):
    username = models.CharField(max_length=150, unique=True, blank=False, null=False, help_text="Admin username")
    is_staff = models.BooleanField(default=False, help_text="Can log into admin site")
    is_superuser = models.BooleanField(default=False, help_text="Has all permissions")
    date_created = models.DateTimeField(default=timezone.now, help_text="When the admin was created")

    objects = AdminUserManager()

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = []

    groups = models.ManyToManyField(
        'auth.Group',
        blank=True,
        related_name='admin_users',
        help_text="The groups this admin belongs to"
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        blank=True,
        related_name='admin_users',
        help_text="Specific permissions for this admin"
    )

    def __str__(self):
        return self.username