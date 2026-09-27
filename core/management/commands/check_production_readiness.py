import os
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import models
from PIL import features

from catalog.models import Category, Product
from core.models import SiteSettings
from orders.models import ShippingZone


class Command(BaseCommand):
    help = "Fail unless business data and production services are ready for launch."

    def handle(self, *args, **options):
        issues = []
        site = SiteSettings.objects.first()
        if not site:
            issues.append("Create SiteSettings in the admin.")
        else:
            for field in ("phone", "whatsapp", "email", "address"):
                if not getattr(site, field, "").strip():
                    issues.append(f"SiteSettings.{field} is empty.")
            for field in ("address_ar", "footer_text_ar", "shipping_message_ar"):
                if not getattr(site, field, "").strip():
                    issues.append(f"SiteSettings.{field} is empty; Arabic storefront copy is required.")
        active_products = Product.objects.filter(is_active=True)
        if not active_products.exists():
            issues.append("There are no active products.")
        if active_products.filter(main_image="").exists():
            issues.append("Every active product must have a main image.")
        missing_product_arabic = active_products.filter(
            models.Q(name_ar="") | models.Q(short_description_ar="") | models.Q(description_ar="")
        ).values_list("sku", flat=True)
        missing_product_arabic = list(missing_product_arabic[:10])
        if missing_product_arabic:
            issues.append(f"Arabic product content is missing for: {', '.join(missing_product_arabic)}.")
        if Category.objects.filter(is_active=True).filter(
            models.Q(name_ar="") | (~models.Q(description="") & models.Q(description_ar=""))
        ).exists():
            issues.append("Every active category must include its applicable Arabic content.")
        missing_product_images = [
            product.sku
            for product in active_products.exclude(main_image="").only("sku", "main_image")
            if not product.main_image.storage.exists(product.main_image.name)
        ]
        if missing_product_images:
            issues.append(f"Product image files are missing for: {', '.join(missing_product_images[:10])}.")
        media_root = Path(settings.MEDIA_ROOT)
        if not media_root.is_dir():
            issues.append(f"MEDIA_ROOT does not exist: {media_root}.")
        elif not os.access(media_root, os.W_OK):
            issues.append(f"MEDIA_ROOT is not writable: {media_root}.")
        if not features.check("webp"):
            issues.append("The installed Pillow package does not support WebP.")
        if not ShippingZone.objects.filter(is_active=True).exists():
            issues.append("Configure at least one active shipping zone.")
        elif ShippingZone.objects.filter(is_active=True, name_ar="").exists():
            issues.append("Every active shipping zone must have an Arabic name.")
        if not settings.ORDER_NOTIFICATION_EMAIL:
            issues.append("ORDER_NOTIFICATION_EMAIL is empty.")
        if not settings.EMAIL_HOST or not settings.EMAIL_HOST_USER or not settings.EMAIL_HOST_PASSWORD:
            issues.append("SMTP credentials are incomplete.")
        if not settings.LEGAL_CONTENT_APPROVED:
            issues.append("Set LEGAL_CONTENT_APPROVED=True after legal review.")
        if not settings.BACKUP_DIRECTORY:
            issues.append("BACKUP_DIRECTORY is empty.")
        elif not Path(settings.BACKUP_DIRECTORY).is_dir():
            issues.append("BACKUP_DIRECTORY does not exist.")
        if settings.DEBUG:
            issues.append("DEBUG must be False.")
        if issues:
            raise CommandError("Production readiness failed:\n- " + "\n- ".join(issues))
        self.stdout.write(self.style.SUCCESS("Production readiness checks passed."))
