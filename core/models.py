from urllib.parse import urlparse
from django.conf import settings
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


class VisitLog(models.Model):
    PATH_TYPES = (
        ("storefront", "المتجر"),
        ("admin", "لوحة الإدارة"),
        ("api", "واجهة API"),
        ("system", "النظام"),
    )

    created_at = models.DateTimeField("وقت الزيارة", auto_now_add=True, db_index=True)
    ip_address = models.GenericIPAddressField("عنوان IP", db_index=True, null=True, blank=True)
    visitor_id = models.CharField("معرف الزائر", max_length=64, db_index=True, blank=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="visit_logs",
        verbose_name="المستخدم المسجل",
    )
    is_authenticated = models.BooleanField("مستخدم مسجل", default=False, db_index=True)
    path = models.CharField("المسار", max_length=500, db_index=True)
    method = models.CharField("طريقة الطلب", max_length=10, default="GET")
    status_code = models.PositiveSmallIntegerField("كود الاستجابة", default=200, db_index=True)
    referer = models.CharField("المصدر / المُحيل", max_length=500, blank=True)
    query_string = models.CharField("معلمات البحث", max_length=500, blank=True)

    is_bot = models.BooleanField("روبوت / زاحف", default=False, db_index=True)
    bot_name = models.CharField("اسم الروبوت", max_length=100, blank=True, db_index=True)

    device_type = models.CharField("نوع الجهاز", max_length=20, default="Desktop", db_index=True)
    browser = models.CharField("المتصفح", max_length=50, blank=True, db_index=True)
    browser_version = models.CharField("إصدار المتصفح", max_length=30, blank=True)
    os = models.CharField("نظام التشغيل", max_length=50, blank=True, db_index=True)
    user_agent = models.TextField("معرّف المتصفح User-Agent", blank=True)

    path_type = models.CharField("نطاق المسار", max_length=20, choices=PATH_TYPES, default="storefront", db_index=True)
    response_time_ms = models.FloatField("وقت الاستجابة (مللي ثانية)", null=True, blank=True)

    class Meta:
        verbose_name = "سجل الزيارة"
        verbose_name_plural = "سجلات الزيارات"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["created_at", "is_bot"]),
            models.Index(fields=["created_at", "is_authenticated"]),
            models.Index(fields=["created_at", "visitor_id"]),
            models.Index(fields=["path_type", "created_at"]),
        ]

    def __str__(self):
        actor = self.user.username if self.user else ("روبوت: " + self.bot_name if self.is_bot else "زائر ضيف")
        return f"{self.created_at:%Y-%m-%d %H:%M} | {actor} | {self.path}"

    @property
    def visitor_category(self):
        if self.is_bot:
            return "bot"
        if self.is_authenticated:
            return "registered"
        return "guest"

    @property
    def visitor_category_label(self):
        if self.is_bot:
            return f"روبوت ({self.bot_name or 'عناكب'})"
        if self.is_authenticated:
            return f"مسجل ({self.user.username if self.user else 'مستخدم'})"
        return "زائر غير مسجل (ضيف)"

    @property
    def referer_domain(self):
        if not self.referer:
            return "مباشر (Direct)"
        try:
            parsed = urlparse(self.referer)
            return parsed.netloc or self.referer
        except Exception:
            return self.referer

