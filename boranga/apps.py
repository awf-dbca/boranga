from django.apps import AppConfig
from django.conf import settings


class BorangaConfig(AppConfig):
    name = "boranga"
    verbose_name = settings.SYSTEM_NAME

    def ready(self):
        from boranga.components.users import signals  # noqa
