import warnings
from io import BytesIO
from pathlib import Path

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.files.base import ContentFile
from django.utils.text import slugify
from PIL import Image, ImageOps, UnidentifiedImageError, features


def _setting_int(name, default, minimum, maximum):
    try:
        value = int(getattr(settings, name, default))
    except (TypeError, ValueError):
        value = default
    return max(minimum, min(value, maximum))


def optimize_image_to_webp(uploaded_file):
    """Return an uploaded image as a same-size, metadata-free WebP ContentFile."""
    if not features.check("webp"):
        raise ValidationError("WebP support is unavailable in the installed Pillow package.")
    quality = _setting_int("IMAGE_WEBP_QUALITY", 82, 45, 95)

    try:
        uploaded_file.seek(0)
        with warnings.catch_warnings():
            warnings.simplefilter("error", Image.DecompressionBombWarning)
            with Image.open(uploaded_file) as source:
                source.load()
                image = ImageOps.exif_transpose(source)

                if getattr(image, "is_animated", False):
                    image.seek(0)

                if image.mode in {"RGBA", "LA"} or "transparency" in image.info:
                    image = image.convert("RGBA")
                else:
                    image = image.convert("RGB")

                output = BytesIO()
                image.save(
                    output,
                    format="WEBP",
                    quality=quality,
                    method=6,
                    optimize=True,
                )
    except (UnidentifiedImageError, OSError, ValueError, Image.DecompressionBombError, Image.DecompressionBombWarning) as exc:
        raise ValidationError("Upload a valid JPG, PNG or WebP image.") from exc

    output.seek(0)
    original_stem = Path(getattr(uploaded_file, "name", "image")).stem or "image"
    safe_stem = slugify(original_stem)[:80] or "image"
    return ContentFile(output.read(), name=f"{safe_stem}.webp")


class OptimizedImageFieldsMixin:
    """Optimize declared ImageFields and remove replaced files after a successful save."""

    optimized_image_fields = ()

    def save(self, *args, **kwargs):
        previous_files = {}
        if self.pk:
            previous = type(self).objects.filter(pk=self.pk).only(*self.optimized_image_fields).first()
            if previous:
                for field_name in self.optimized_image_fields:
                    old_file = getattr(previous, field_name)
                    if old_file and old_file.name:
                        previous_files[field_name] = (old_file.storage, old_file.name)

        update_fields = kwargs.get("update_fields")
        processed_fields = []
        for field_name in self.optimized_image_fields:
            image_file = getattr(self, field_name)
            should_process = image_file and not getattr(image_file, "_committed", True)
            if update_fields is not None and field_name not in update_fields:
                should_process = False
            if should_process:
                setattr(self, field_name, optimize_image_to_webp(image_file))
                processed_fields.append(field_name)

        try:
            super().save(*args, **kwargs)
        except Exception:
            for field_name in processed_fields:
                new_file = getattr(self, field_name)
                if getattr(new_file, "_committed", False) and new_file.name and new_file.storage.exists(new_file.name):
                    new_file.storage.delete(new_file.name)
            raise

        for field_name, (storage, old_name) in previous_files.items():
            if update_fields is not None and field_name not in update_fields:
                continue
            current_file = getattr(self, field_name)
            current_name = current_file.name if current_file else ""
            if old_name != current_name and storage.exists(old_name):
                storage.delete(old_name)
