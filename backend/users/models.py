from django.contrib.auth.models import AbstractUser, AbstractBaseUser, PermissionsMixin, BaseUserManager
from django.db import models
from django.utils import timezone

class User(AbstractUser):
    # Core fields
    email = models.EmailField(unique=True, blank=False, null=False, help_text="User's email from Twitch")
    twitch_id = models.CharField(max_length=25, unique=True, blank=False, null=False, help_text="Unique Twitch user ID")
    username = models.CharField(max_length=150, unique=True, blank=False, null=False, help_text="Username from Twitch")
    display_name = models.CharField(max_length=150, blank=True, null=True, help_text="Display name from Twitch")
    first_name = models.CharField(max_length=150, blank=True, null=True, help_text="User's first name from Twitch")
    last_name = models.CharField(max_length=150, blank=True, null=True, help_text="User's last name from Twitch")
    twitch_channel_url = models.URLField(blank=False, null=False, help_text="Twitch channel URL")

    # Timestamps
    date_created = models.DateTimeField(default=timezone.now, help_text="When the user was created")
    date_updated = models.DateTimeField(auto_now=True, help_text="Last update time")

    # Change log (stored as text for simplicity)
    changes_log = models.TextField(blank=True, null=True, help_text="Log of changes to user data")

    # Authentication settings
    USERNAME_FIELD = 'email' # Login with email instead of username
    REQUIRED_FIELDS = ['twitch_id'] # Twitch ID is required;

    def update_from_twitch(self, twitch_data):
        """
        Update user fields from Twitch API data and log changes.
        Args:
            twitch_data (dict): Data from Twitch API (e.g., {'id': '123', 'login': 'user', ...}})
        """
        changed = False
        log_entries = []

        # Update fields if the differ
        if self.twitch_id != twitch_data.get('id'):
            log_entries.append(f"Twitch ID changed: {self.twitch_id} -> {twitch_data.get('id')}")
            self.twitch_id = twitch_data.get('id')
            changed = True

        if self.email != twitch_data.get('email'):
            log_entries.append(f"Email changed: {self.email} -> {twitch_data.get('email')}")
            self.email = twitch_data.get('email')
            changed = True

        new_display_name = twitch_data.get('display_name') or twitch_data.get('login')
        if self.display_name != new_display_name:
            log_entries.append(f"Display name changed: {self.display_name} -> {new_display_name}")
            self.display_name = new_display_name
            changed = True

        # Twitch login as username fallback
        twitch_login = twitch_data.get('login')
        if self.username != twitch_login:
            log_entries.append(f"Username changed: {self.username} -> {twitch_login}")
            self.username = twitch_login
            changed = True

        # Construct channel URL
        new_channel_url = f"https://twitch.tv/{twitch_login}"
        if self.twitch_channel_url != new_channel_url:
            log_entries.append(f"Channel URL changed: {self.twitch_channel_url} -> {new_channel_url}")
            self.twitch_channel_url = new_channel_url
            changed = True

        # Update changes log if there were changes
        if changed: 
            current_log = self.changes_log or ""
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
        related_name='adminuser_groups',
        help_text="The groups this admin belongs to"
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        blank=True,
        related_name='adminuser_permissions',
        help_text="Specific permissions for this admin"
    )

    def __str__(self):
        return self.username