from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.utils import translation

from catalog.models import Category, Product
from core.models import SiteSettings


class Command(BaseCommand):
    help = "Read-only SEO content audit; use --strict to fail when issues remain."

    def add_arguments(self, parser):
        parser.add_argument("--strict", action="store_true")

    def handle(self, *args, **options):
        issues = []
        if not settings.SITE_URL:
            issues.append("Set SITE_URL=https://rocks-ev.com in production.")
        site = SiteSettings.objects.first()
        if not site:
            issues.append("Create real business contact details in SiteSettings.")
        else:
            for field in ("phone", "email", "address", "address_ar"):
                if not getattr(site, field).strip():
                    issues.append(f"Missing business field: {field}.")
            if not any((site.facebook, site.instagram, site.tiktok)):
                issues.append("Add verified official social profiles to establish the brand identity.")
        categories = list(Category.objects.filter(is_active=True))
        products = list(Product.objects.filter(is_active=True, category__is_active=True).select_related("category"))
        if not products:
            issues.append("There are no publicly available products.")
        for label, items, fields in (
            ("category", categories, ("name_ar", "description", "description_ar")),
            ("product", products, ("name_ar", "short_description", "short_description_ar", "description", "description_ar")),
        ):
            for item in items:
                for field in fields:
                    if not getattr(item, field).strip():
                        issues.append(f"{label} {item.slug}: missing {field}.")
            for code in ("en", "ar"):
                seen = {}
                with translation.override(code):
                    for item in items:
                        title = item.display_meta_title.strip()
                        if title in seen:
                            issues.append(f"Duplicate {code} {label} title: {seen[title]} and {item.slug}.")
                        seen[title] = item.slug
                        if len(title) > 70:
                            issues.append(f"{label} {item.slug}: {code} title exceeds 70 characters; review likely truncation.")
                        if not item.display_meta_description.strip():
                            issues.append(f"{label} {item.slug}: empty {code} search description.")
        for product in products:
            if not product.main_image:
                issues.append(f"product {product.slug}: missing main image.")
        self.stdout.write(f"Audited {len(categories)} active categories and {len(products)} public products.")
        for issue in issues:
            self.stdout.write(self.style.WARNING("- " + issue))
        if issues and options["strict"]:
            raise CommandError(f"SEO audit found {len(issues)} issues.")
        self.stdout.write(f"{len(issues)} content/configuration issues. Live indexing and ranking require Search Console verification.")
