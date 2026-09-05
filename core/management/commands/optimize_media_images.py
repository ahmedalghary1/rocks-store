from pathlib import Path

from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand, CommandError

from catalog.models import Category, Product, ProductImage
from marketing.models import Banner


IMAGE_FIELDS = (
    (Category, "image"),
    (Product, "main_image"),
    (ProductImage, "image"),
    (Banner, "image"),
    (Banner, "mobile_image"),
)


class Command(BaseCommand):
    help = "Convert existing uploaded catalog and banner images to compressed WebP files"

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true", help="Report images without changing files")
        parser.add_argument("--force", action="store_true", help="Recompress images that are already WebP")

    def handle(self, *args, **options):
        converted = skipped = missing = failed = 0

        for model, field_name in IMAGE_FIELDS:
            queryset = model.objects.exclude(**{field_name: ""}).only("pk", field_name)
            for instance in queryset.iterator():
                field_file = getattr(instance, field_name)
                old_name = field_file.name
                if not options["force"] and Path(old_name).suffix.lower() == ".webp":
                    skipped += 1
                    continue
                if not field_file.storage.exists(old_name):
                    missing += 1
                    self.stderr.write(f"Missing: {model.__name__} #{instance.pk} — {old_name}")
                    continue
                if options["dry_run"]:
                    self.stdout.write(f"Would convert: {old_name}")
                    converted += 1
                    continue

                try:
                    with field_file.storage.open(old_name, "rb") as source:
                        uploaded = ContentFile(source.read(), name=Path(old_name).name)
                    setattr(instance, field_name, uploaded)
                    instance.save(update_fields=(field_name,))
                    converted += 1
                    self.stdout.write(self.style.SUCCESS(f"Converted: {old_name}"))
                except Exception as exc:
                    failed += 1
                    self.stderr.write(self.style.ERROR(f"Failed: {old_name} — {exc}"))

        self.stdout.write(
            self.style.SUCCESS(
                f"Finished. Converted: {converted}; skipped WebP: {skipped}; missing: {missing}; failed: {failed}."
            )
        )
        if failed:
            raise CommandError(f"Could not convert {failed} image(s). Originals were kept for failed conversions.")
