from django.db import models


class Banner(models.Model):
    LOCATIONS = [("hero", "الرئيسية"), ("offer", "عرض"), ("promo", "ترويجي")]
    title = models.CharField(max_length=160)
    subtitle = models.CharField(max_length=255, blank=True)
    image = models.ImageField(upload_to="banners/", blank=True)
    mobile_image = models.ImageField(upload_to="banners/", blank=True)
    link = models.CharField(max_length=255, blank=True)
    button_text = models.CharField(max_length=60, blank=True)
    location = models.CharField(max_length=20, choices=LOCATIONS, default="promo")
    sort_order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    start_date = models.DateTimeField(null=True, blank=True)
    end_date = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ("sort_order",)

    def __str__(self):
        return self.title
