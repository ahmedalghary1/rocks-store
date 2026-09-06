from django.db import models
from django.utils import translation
from django.core.exceptions import ValidationError
from django.core.validators import URLValidator
from catalog.validators import validate_image_size
from core.image_processing import OptimizedImageFieldsMixin


def validate_banner_link(value):
    if not value or value.startswith("/") or value.startswith("#"):
        return
    try:
        URLValidator(schemes=("http", "https"))(value)
    except ValidationError:
        raise ValidationError("Use an internal link or a valid HTTP/HTTPS URL.")


class Banner(OptimizedImageFieldsMixin, models.Model):
    optimized_image_fields = ("image", "mobile_image")
    LOCATIONS = [("hero", "Home hero"), ("offer", "Offer"), ("promo", "Promotional")]
    title = models.CharField(max_length=160)
    title_ar = models.CharField("العنوان بالعربية", max_length=160, blank=True)
    subtitle = models.CharField(max_length=255, blank=True)
    subtitle_ar = models.CharField("العنوان الفرعي بالعربية", max_length=255, blank=True)
    image = models.ImageField(upload_to="banners/", blank=True, validators=[validate_image_size])
    mobile_image = models.ImageField(upload_to="banners/", blank=True, validators=[validate_image_size])
    link = models.CharField(max_length=255, blank=True, validators=[validate_banner_link])
    button_text = models.CharField(max_length=60, blank=True)
    button_text_ar = models.CharField("نص الزر بالعربية", max_length=60, blank=True)
    location = models.CharField(max_length=20, choices=LOCATIONS, default="promo")
    sort_order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    start_date = models.DateTimeField(null=True, blank=True)
    end_date = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ("sort_order",)

    def __str__(self):
        return self.title

    def _localized(self, field_name):
        if translation.get_language() == "ar":
            return getattr(self, f"{field_name}_ar", "") or getattr(self, field_name)
        return getattr(self, field_name)

    @property
    def display_title(self):
        return self._localized("title")

    @property
    def display_subtitle(self):
        return self._localized("subtitle")

    @property
    def display_button_text(self):
        return self._localized("button_text")


class Subscriber(models.Model):
    email = models.EmailField(unique=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-created_at",)

    def __str__(self):
        return self.email
