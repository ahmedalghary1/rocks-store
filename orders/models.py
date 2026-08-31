import uuid
from decimal import Decimal
from django.conf import settings
from django.db import models
from django.utils import timezone


class Coupon(models.Model):
    TYPES = (("percentage", "نسبة"), ("fixed", "قيمة ثابتة"))
    code = models.CharField(max_length=40, unique=True)
    discount_type = models.CharField(max_length=20, choices=TYPES)
    value = models.DecimalField(max_digits=10, decimal_places=2)
    minimum_order = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    usage_limit = models.PositiveIntegerField(default=100)
    usage_count = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    def discount_for(self, subtotal):
        now = timezone.now()
        if not self.is_active or not self.start_date <= now <= self.end_date or self.usage_count >= self.usage_limit or subtotal < self.minimum_order:
            return Decimal("0")
        amount = subtotal * self.value / 100 if self.discount_type == "percentage" else self.value
        return min(amount, subtotal)


class Order(models.Model):
    STATUSES = (("pending", "قيد المراجعة"), ("confirmed", "تم التأكيد"), ("processing", "قيد التجهيز"), ("shipped", "تم الشحن"), ("delivered", "تم التسليم"), ("cancelled", "ملغي"))
    PAYMENT = (("cod", "الدفع عند الاستلام"), ("bank", "تحويل بنكي"))
    order_number = models.CharField(max_length=32, unique=True, db_index=True)
    public_token = models.UUIDField(default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="orders")
    customer_name = models.CharField(max_length=160)
    phone = models.CharField(max_length=30)
    second_phone = models.CharField(max_length=30, blank=True)
    governorate = models.CharField(max_length=80)
    city = models.CharField(max_length=80)
    address = models.CharField(max_length=255)
    notes = models.TextField(blank=True)
    subtotal = models.DecimalField(max_digits=12, decimal_places=2)
    shipping_cost = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    discount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=12, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUSES, default="pending", db_index=True)
    payment_method = models.CharField(max_length=20, choices=PAYMENT, default="cod")
    payment_status = models.CharField(max_length=20, default="unpaid")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-created_at",)

    def __str__(self):
        return self.order_number


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey("catalog.Product", null=True, on_delete=models.SET_NULL)
    variant = models.ForeignKey("catalog.ProductVariant", null=True, blank=True, on_delete=models.SET_NULL)
    product_name = models.CharField(max_length=180)
    sku = models.CharField(max_length=60)
    price = models.DecimalField(max_digits=12, decimal_places=2)
    quantity = models.PositiveIntegerField()
    total = models.DecimalField(max_digits=12, decimal_places=2)
