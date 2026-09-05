from django.db import models
from django.utils import translation


class SiteSettings(models.Model):
    company_name = models.CharField(max_length=120, default="ROCKS ELECTRIC")
    phone = models.CharField(max_length=30, blank=True)
    whatsapp = models.CharField(max_length=30, blank=True)
    email = models.EmailField(blank=True)
    address = models.CharField(max_length=255, blank=True)
    address_ar = models.CharField("العنوان بالعربية", max_length=255, blank=True)
    facebook = models.URLField(blank=True)
    instagram = models.URLField(blank=True)
    tiktok = models.URLField(blank=True)
    footer_text = models.CharField(max_length=255, default="Powering a cleaner tomorrow.")
    footer_text_ar = models.CharField("نص التذييل بالعربية", max_length=255, blank=True)
    shipping_message = models.CharField(max_length=160, default="Fast delivery across Egypt")
    shipping_message_ar = models.CharField("رسالة الشحن بالعربية", max_length=160, blank=True)
    currency = models.CharField(max_length=12, default="EGP")

    class Meta:
        verbose_name = "Site settings"
        verbose_name_plural = "Site settings"

    def __str__(self):
        return self.company_name

    def save(self, *args, **kwargs):
        if not self.pk and SiteSettings.objects.exists():
            self.pk = SiteSettings.objects.values_list("pk", flat=True).first()
        super().save(*args, **kwargs)

    def _localized(self, field_name):
        if translation.get_language() == "ar":
            return getattr(self, f"{field_name}_ar", "") or getattr(self, field_name)
        return getattr(self, field_name)

    @property
    def display_address(self):
        return self._localized("address")

    @property
    def display_footer_text(self):
        return self._localized("footer_text")

    @property
    def display_shipping_message(self):
        return self._localized("shipping_message")


class ContactMessage(models.Model):
    name = models.CharField(max_length=120)
    phone = models.CharField(max_length=30)
    email = models.EmailField(blank=True)
    subject = models.CharField(max_length=160)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.name} — {self.subject}"
