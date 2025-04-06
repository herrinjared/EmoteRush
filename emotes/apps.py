from django.apps import AppConfig


class EmotesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'emotes'

    def ready(self):
        import emotes.signals