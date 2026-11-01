import re
import uuid
from decimal import Decimal
from django.conf import settings
from django.utils import timezone
from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from catalog.models import Product, ProductVariant
from orders.models import Coupon, Order, OrderItem, ShippingZone
from orders.forms import resolve_shipping_zone


class ShippingZoneSerializer(serializers.ModelSerializer):
    display_name = serializers.CharField(read_only=True)

    class Meta:
        model = ShippingZone
        fields = (
            "id",
            "name",
            "name_ar",
            "display_name",
            "shipping_cost",
            "free_shipping_threshold",
            "sort_order",
        )


class CouponValidateSerializer(serializers.Serializer):
    code = serializers.CharField(required=True)
    subtotal = serializers.DecimalField(max_digits=12, decimal_places=2, required=True, min_value=Decimal("0.00"))


class CouponValidateResponseSerializer(serializers.Serializer):
    valid = serializers.BooleanField()
    code = serializers.CharField()
    discount_type = serializers.CharField(allow_blank=True, required=False)
    value = serializers.DecimalField(max_digits=10, decimal_places=2, required=False)
    discount_amount = serializers.DecimalField(max_digits=12, decimal_places=2)
    message = serializers.CharField()


class OrderItemSerializer(serializers.ModelSerializer):
    display_product_name = serializers.CharField(read_only=True)

    class Meta:
        model = OrderItem
        fields = (
            "id",
            "product",
            "variant",
            "product_name",
            "product_name_ar",
            "display_product_name",
            "sku",
            "price",
            "quantity",
            "total",
        )


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    payment_status_display = serializers.CharField(source="get_payment_status_display", read_only=True)

    class Meta:
        model = Order
        fields = (
            "id",
            "order_number",
            "public_token",
            "customer_name",
            "phone",
            "second_phone",
            "email",
            "governorate",
            "city",
            "address",
            "notes",
            "subtotal",
            "shipping_cost",
            "discount",
            "total",
            "status",
            "status_display",
            "payment_method",
            "payment_status",
            "payment_status_display",
            "items",
            "created_at",
            "updated_at",
        )


class DirectOrderItemInputSerializer(serializers.Serializer):
    product_id = serializers.IntegerField(required=True)
    variant_id = serializers.IntegerField(required=False, allow_null=True, default=None)
    quantity = serializers.IntegerField(required=False, default=1, min_value=1)


class OrderCreateSerializer(serializers.Serializer):
    customer_name = serializers.CharField(required=True, max_length=160)
    phone = serializers.CharField(required=True, max_length=30)
    second_phone = serializers.CharField(required=False, allow_blank=True, max_length=30, default="")
    email = serializers.EmailField(required=False, allow_blank=True, default="")
    governorate = serializers.CharField(required=True, max_length=80)
    city = serializers.CharField(required=True, max_length=80)
    address = serializers.CharField(required=True, max_length=255)
    notes = serializers.CharField(required=False, allow_blank=True, default="")
    checkout_token = serializers.UUIDField(required=False, default=uuid.uuid4)
    coupon_code = serializers.CharField(required=False, allow_blank=True, max_length=40, default="")
    items = DirectOrderItemInputSerializer(many=True, required=False, default=list)

    def validate_phone(self, value):
        cleaned = value.replace(" ", "")
        if len(cleaned) < 10 or not cleaned.lstrip("+").isdigit():
            raise serializers.ValidationError("Enter a valid phone number (at least 10 digits).")
        return cleaned

    def validate_second_phone(self, value):
        if not value:
            return ""
        cleaned = value.replace(" ", "")
        if len(cleaned) < 10 or not cleaned.lstrip("+").isdigit():
            raise serializers.ValidationError("Enter a valid alternative phone number.")
        return cleaned

    def validate_governorate(self, value):
        zone = resolve_shipping_zone(value)
        if not zone:
            raise serializers.ValidationError(
                f"Delivery zone '{value}' is not supported. Please select a valid Egyptian governorate."
            )
        self.shipping_zone = zone
        return zone.name


class OrderTrackInputSerializer(serializers.Serializer):
    order_number = serializers.CharField(required=True, max_length=40)
    phone = serializers.CharField(required=True, max_length=30)

    def validate_phone(self, value):
        return value.replace(" ", "")


class OrderTrackResponseSerializer(serializers.ModelSerializer):
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    items_count = serializers.SerializerMethodField()

    class Meta:
        model = Order
        fields = (
            "order_number",
            "public_token",
            "customer_name",
            "governorate",
            "city",
            "status",
            "status_display",
            "total",
            "created_at",
            "items_count",
        )

    @extend_schema_field(serializers.IntegerField)
    def get_items_count(self, obj):
        return obj.items.count()

