from django.apps import AppConfig


class MarketingConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "marketing"

    def ready(self):
        from core.media_cleanup import register_media_cleanup
        from .models import Banner

        register_media_cleanup(Banner, ("image", "mobile_image"))
