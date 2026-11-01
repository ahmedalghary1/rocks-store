from decimal import Decimal
from django.conf import settings
from rest_framework import serializers

from catalog.models import Product, ProductVariant


class CartItemSerializer(serializers.Serializer):
    key = serializers.CharField(read_only=True)
    product_id = serializers.IntegerField(read_only=True)
    product_name = serializers.CharField(read_only=True)
    product_name_ar = serializers.CharField(read_only=True)
    display_product_name = serializers.CharField(read_only=True)
    product_slug = serializers.CharField(read_only=True)
    product_image = serializers.CharField(read_only=True, allow_null=True)
    variant_id = serializers.IntegerField(read_only=True, allow_null=True)
    variant_label = serializers.CharField(read_only=True, allow_null=True)
    variant_label_ar = serializers.CharField(read_only=True, allow_null=True)
    display_variant_label = serializers.CharField(read_only=True, allow_null=True)
    sku = serializers.CharField(read_only=True)
    price = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    quantity = serializers.IntegerField(read_only=True)
    stock_quantity = serializers.IntegerField(read_only=True)
    total = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)


class CartCouponSerializer(serializers.Serializer):
    code = serializers.CharField(read_only=True)
    discount_type = serializers.CharField(read_only=True)
    value = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    discount_amount = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)


class CartSerializer(serializers.Serializer):
    items = CartItemSerializer(many=True, read_only=True)
    count = serializers.IntegerField(read_only=True)
    subtotal = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    shipping = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    free_shipping_threshold = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    coupon = CartCouponSerializer(read_only=True, allow_null=True)
    discount = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    total = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)


class AddToCartSerializer(serializers.Serializer):
    product_id = serializers.IntegerField(required=True)
    variant_id = serializers.IntegerField(required=False, allow_null=True, default=None)
    quantity = serializers.IntegerField(required=False, default=1, min_value=1)

    def validate(self, attrs):
        product_id = attrs["product_id"]
        variant_id = attrs.get("variant_id")
        try:
            product = Product.objects.get(pk=product_id, is_active=True)
        except Product.DoesNotExist:
            raise serializers.ValidationError({"product_id": "Product not found or inactive."})

        if product.is_coming_soon:
            raise serializers.ValidationError({"product_id": "This product is coming soon."})

        variant = None
        if variant_id:
            try:
                variant = ProductVariant.objects.get(pk=variant_id, product=product, is_active=True)
            except ProductVariant.DoesNotExist:
                raise serializers.ValidationError({"variant_id": "Selected variant does not exist for this product."})
        elif product.variants.filter(is_active=True).exists():
            raise serializers.ValidationError({"variant_id": "Please select a product variant (length / option) before adding to cart."})

        available = variant.stock_quantity if variant else product.stock_quantity
        if available <= 0:
            raise serializers.ValidationError("This item is currently out of stock.")

        price = variant.price if variant and variant.price is not None else product.price
        if price is None:
            raise serializers.ValidationError("This item does not have a price configured yet.")

        attrs["product"] = product
        attrs["variant"] = variant
        return attrs


class UpdateCartItemSerializer(serializers.Serializer):
    quantity = serializers.IntegerField(required=True, min_value=0)


class ApplyCouponSerializer(serializers.Serializer):
    code = serializers.CharField(required=True, max_length=40)

