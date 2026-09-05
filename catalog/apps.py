from django.apps import AppConfig


class CatalogConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "catalog"

    def ready(self):
        from core.media_cleanup import register_media_cleanup
        from .models import Category, Product, ProductImage

        register_media_cleanup(Category, ("image",))
        register_media_cleanup(Product, ("main_image",))
        register_media_cleanup(ProductImage, ("image",))
