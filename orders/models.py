import uuid
from decimal import Decimal
from django.conf import settings
from django.core.validators import MinValueValidator
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import F, Q
from django.utils import timezone


class Coupon(models.Model):
    TYPES = (("percentage", "نسبة"), ("fixed", "قيمة ثابتة"))
    code = models.CharField(max_length=40, unique=True)
    discount_type = models.CharField(max_length=20, choices=TYPES)
    value = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal("0.01"))])
    minimum_order = models.DecimalField(max_digits=12, decimal_places=2, default=0, validators=[MinValueValidator(Decimal("0"))])
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    usage_limit = models.PositiveIntegerField(default=100)
    usage_count = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        constraints = [
            models.CheckConstraint(condition=Q(value__gt=0), name="coupon_value_positive"),
            models.CheckConstraint(condition=Q(minimum_order__gte=0), name="coupon_minimum_nonnegative"),
            models.CheckConstraint(condition=Q(end_date__gt=F("start_date")), name="coupon_dates_valid"),
            models.CheckConstraint(condition=Q(discount_type="fixed") | Q(value__lte=100), name="coupon_percentage_max_100"),
        ]

    def discount_for(self, subtotal):
        now = timezone.now()
        if not self.is_active or not self.start_date <= now <= self.end_date or self.usage_count >= self.usage_limit or subtotal < self.minimum_order:
            return Decimal("0")
        amount = subtotal * self.value / 100 if self.discount_type == "percentage" else self.value
        return min(amount, subtotal)


class Order(models.Model):
    STATUSES = (("pending", "قيد المراجعة"), ("confirmed", "تم التأكيد"), ("processing", "قيد التجهيز"), ("shipped", "تم الشحن"), ("delivered", "تم التسليم"), ("cancelled", "ملغي"))
    PAYMENT = (("cod", "الدفع عند الاستلام"),)
    PAYMENT_STATUSES = (("unpaid", "غير مدفوع"), ("pending", "قيد المراجعة"), ("paid", "مدفوع"), ("refunded", "مسترد"))
    order_number = models.CharField(max_length=40, unique=True, db_index=True)
    public_token = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    checkout_token = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="orders")
    coupon = models.ForeignKey(Coupon, null=True, blank=True, on_delete=models.PROTECT, related_name="orders")
    customer_name = models.CharField(max_length=160)
    phone = models.CharField(max_length=30)
    email = models.EmailField(blank=True)
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
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUSES, default="unpaid")
    stock_restored = models.BooleanField(default=False, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-created_at",)
        constraints = [
            models.CheckConstraint(condition=Q(payment_method="cod"), name="order_payment_method_cod"),
        ]

    def __str__(self):
        return self.order_number

    def clean(self):
        super().clean()
        if self.payment_method != "cod":
            raise ValidationError({"payment_method": "طريقة الدفع المتاحة هي الدفع عند الاستلام فقط."})
        if self.pk:
            previous = Order.objects.filter(pk=self.pk).values_list("status", flat=True).first()
            if previous == "cancelled" and self.status != "cancelled":
                raise ValidationError({"status": "لا يمكن إعادة فتح طلب ملغي بعد إعادة المخزون."})


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey("catalog.Product", null=True, on_delete=models.PROTECT)
    variant = models.ForeignKey("catalog.ProductVariant", null=True, blank=True, on_delete=models.PROTECT)
    product_name = models.CharField(max_length=180)
    sku = models.CharField(max_length=60)
    price = models.DecimalField(max_digits=12, decimal_places=2)
    quantity = models.PositiveIntegerField()
    total = models.DecimalField(max_digits=12, decimal_places=2)

    class Meta:
        constraints = [
            models.CheckConstraint(condition=Q(quantity__gt=0), name="order_item_quantity_positive"),
            models.CheckConstraint(condition=Q(price__gte=0), name="order_item_price_nonnegative"),
            models.CheckConstraint(condition=Q(total__gte=0), name="order_item_total_nonnegative"),
        ]


class ShippingZone(models.Model):
    name = models.CharField(max_length=80, unique=True)
    shipping_cost = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(Decimal("0"))])
    free_shipping_threshold = models.DecimalField(
        max_digits=12, decimal_places=2, null=True, blank=True,
        validators=[MinValueValidator(Decimal("0"))],
    )
    is_active = models.BooleanField(default=True)
    sort_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ("sort_order", "name")
        constraints = [
            models.CheckConstraint(condition=Q(shipping_cost__gte=0), name="shipping_zone_cost_nonnegative"),
            models.CheckConstraint(
                condition=Q(free_shipping_threshold__isnull=True) | Q(free_shipping_threshold__gte=0),
                name="shipping_zone_threshold_nonnegative",
            ),
        ]

    def __str__(self):
        return self.name

    def cost_for(self, subtotal):
        if self.free_shipping_threshold is not None and subtotal >= self.free_shipping_threshold:
            return Decimal("0")
        return self.shipping_cost


class OrderNotification(models.Model):
    STATUSES = (
        ("pending", "قيد الإرسال"), ("sending", "جارٍ الإرسال"), ("sent", "تم الإرسال"),
        ("failed", "فشل الإرسال"), ("skipped", "لا يوجد مستلمون"),
    )
    order = models.OneToOneField(Order, on_delete=models.CASCADE, related_name="notification")
    status = models.CharField(max_length=20, choices=STATUSES, default="pending", db_index=True)
    attempts = models.PositiveIntegerField(default=0)
    last_error = models.TextField(blank=True)
    last_attempt_at = models.DateTimeField(null=True, blank=True)
    sent_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.order.order_number}: {self.get_status_display()}"
