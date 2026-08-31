from django.db import models


class SiteSettings(models.Model):
    company_name = models.CharField(max_length=120, default="ROCKS ELECTRIC")
    phone = models.CharField(max_length=30, default="0100 000 0000")
    whatsapp = models.CharField(max_length=30, default="201000000000")
    email = models.EmailField(default="hello@rocks-electric.com")
    address = models.CharField(max_length=255, default="القاهرة، مصر")
    facebook = models.URLField(blank=True)
    instagram = models.URLField(blank=True)
    tiktok = models.URLField(blank=True)
    footer_text = models.CharField(max_length=255, default="حلول كهربائية مختارة لتدوم.")
    shipping_message = models.CharField(max_length=160, default="شحن سريع لكل محافظات مصر")
    currency = models.CharField(max_length=12, default="ج.م")

    class Meta:
        verbose_name = "إعدادات الموقع"
        verbose_name_plural = "إعدادات الموقع"

    def __str__(self):
        return self.company_name


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
