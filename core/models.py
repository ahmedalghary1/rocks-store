from django.db import models


class SiteSettings(models.Model):
    company_name = models.CharField(max_length=120, default="ROCKS ELECTRIC")
    phone = models.CharField(max_length=30, blank=True)
    whatsapp = models.CharField(max_length=30, blank=True)
    email = models.EmailField(blank=True)
    address = models.CharField(max_length=255, blank=True)
    facebook = models.URLField(blank=True)
    instagram = models.URLField(blank=True)
    tiktok = models.URLField(blank=True)
    footer_text = models.CharField(max_length=255, default="حلول كهربائية مختارة لتدوم.")
    shipping_message = models.CharField(max_length=160, default="شحن سريع لكل محافظات مصر")
    currency = models.CharField(max_length=12, default="ج.م")
    bank_instructions = models.TextField(blank=True, help_text="تظهر فقط عند تفعيل التحويل البنكي في صفحة الدفع.")

    class Meta:
        verbose_name = "إعدادات الموقع"
        verbose_name_plural = "إعدادات الموقع"

    def __str__(self):
        return self.company_name

    def save(self, *args, **kwargs):
        if not self.pk and SiteSettings.objects.exists():
            self.pk = SiteSettings.objects.values_list("pk", flat=True).first()
        super().save(*args, **kwargs)


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
