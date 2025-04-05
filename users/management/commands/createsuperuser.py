from django.core.management.base import BaseCommand
from users.models import AdminUser
from django.contrib.auth.management.commands import createsuperuser
from django.core.management import CommandError

class Command(BaseCommand):
    help = 'Create a superuser for the AdminUser model'

    def add_arguments(self, parser):
        parser.add_argument('--username', dest='username', default=None, help='Specifies the username for the superuser.')
        parser.add_argument('--noinput', '--no-input', action='store_false', dest='interactive', help='Do not prompt the user for input.')

    def handle(self, *args, **options):
        username = options.get('username')
        interactive = options.get('interactive')

        if not interactive and not username:
            raise CommandError("You must provide --username when using --noinput.")

        # Use AdminUserManager directly
        manager = AdminUser.objects

        if interactive:
            # Prompt for username
            while not username:
                username = input("Username: ").strip()
                if not username:
                    self.stderr.write("Error: This field cannot be blank.")
                elif AdminUser.objects.filter(username=username).exists():
                    self.stderr.write("Error: A user with that username already exists.")
                    username = None

            # Prompt for password
            password = None
            while not password:
                password = self.get_input_data("Password: ", is_password=True)
                password2 = self.get_input_data("Password (again): ", is_password=True)
                if password != password2:
                    self.stderr.write("Error: Your passwords didn't match.")
                    password = None
                elif len(password) < 8:
                    self.stderr.write("This password is too short. It must contain at least 8 characters.")
                    bypass = input("Bypass password validation and create user anyway? [y/N]: ").lower() == 'y'
                    if not bypass:
                        password = None

            # Create the superuser
            manager.create_superuser(username=username, password=password)
            self.stdout.write(self.style.SUCCESS(f"Superuser '{username}' created successfully."))
        else:
            # Non-interactive mode
            password = options.get('password') or input("Password: ")
            manager.create_superuser(username=username, password=password)
            self.stdout.write(self.style.SUCCESS(f"Superuser '{username}' created successfully."))

    def get_input_data(self, prompt, is_password=False):
        from getpass import getpass
        return getpass(prompt) if is_password else input(prompt).strip()