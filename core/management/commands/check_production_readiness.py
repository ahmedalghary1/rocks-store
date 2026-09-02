from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from catalog.models import Product
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
        active_products = Product.objects.filter(is_active=True)
        if not active_products.exists():
            issues.append("There are no active products.")
        if active_products.filter(main_image="").exists():
            issues.append("Every active product must have a main image.")
        if not ShippingZone.objects.filter(is_active=True).exists():
            issues.append("Configure at least one active shipping zone.")
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
