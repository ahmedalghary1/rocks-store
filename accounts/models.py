from django.conf import settings
from django.db import models


class Address(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="addresses")
    label = models.CharField(max_length=60, default="Home")
    recipient_name = models.CharField(max_length=160)
    phone = models.CharField(max_length=30)
    governorate = models.CharField(max_length=80)
    city = models.CharField(max_length=80)
    address_line = models.CharField(max_length=255)
    is_default = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.label} — {self.recipient_name}"
