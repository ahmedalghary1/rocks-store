from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from catalog.models import (
    Category,
    Product,
    ProductImage,
    ProductSpecification,
    ProductVariant,
    HomepageProduct,
)


class CategoryMinimalSerializer(serializers.ModelSerializer):
    display_name = serializers.CharField(read_only=True)

    class Meta:
        model = Category
        fields = ("id", "name", "name_ar", "slug", "display_name")


class CategorySerializer(serializers.ModelSerializer):
    display_name = serializers.CharField(read_only=True)
    display_description = serializers.CharField(read_only=True)
    products_count = serializers.IntegerField(read_only=True, default=0)

    class Meta:
        model = Category
        fields = (
            "id",
            "name",
            "name_ar",
            "slug",
            "description",
            "description_ar",
            "meta_title",
            "meta_title_ar",
            "meta_description",
            "meta_description_ar",
            "image",
            "icon",
            "parent",
            "is_active",
            "sort_order",
            "display_name",
            "display_description",
            "products_count",
        )


class ProductImageSerializer(serializers.ModelSerializer):
    display_alt_text = serializers.CharField(read_only=True)

    class Meta:
        model = ProductImage
        fields = ("id", "image", "alt_text", "alt_text_ar", "display_alt_text", "sort_order")


class ProductSpecificationSerializer(serializers.ModelSerializer):
    display_name = serializers.CharField(read_only=True)
    display_value = serializers.CharField(read_only=True)

    class Meta:
        model = ProductSpecification
        fields = ("id", "name", "name_ar", "value", "value_ar", "display_name", "display_value", "sort_order")


class ProductVariantSerializer(serializers.ModelSerializer):
    display_label = serializers.CharField(read_only=True)
    in_stock = serializers.SerializerMethodField()

    class Meta:
        model = ProductVariant
        fields = (
            "id",
            "sku",
            "label",
            "label_ar",
            "display_label",
            "price",
            "stock_quantity",
            "attributes",
            "is_active",
            "in_stock",
        )

    @extend_schema_field(serializers.BooleanField)
    def get_in_stock(self, obj):
        return obj.stock_quantity > 0


class ProductListSerializer(serializers.ModelSerializer):
    display_name = serializers.CharField(read_only=True)
    display_short_description = serializers.CharField(read_only=True)
    category = CategoryMinimalSerializer(read_only=True)
    discount_percentage = serializers.IntegerField(read_only=True)
    in_stock = serializers.BooleanField(read_only=True)
    has_variant_price = serializers.BooleanField(read_only=True)
    has_price_options = serializers.BooleanField(read_only=True)

    class Meta:
        model = Product
        fields = (
            "id",
            "name",
            "name_ar",
            "slug",
            "sku",
            "category",
            "short_description",
            "short_description_ar",
            "display_name",
            "display_short_description",
            "price",
            "old_price",
            "discount_percentage",
            "main_image",
            "is_featured",
            "is_best_seller",
            "is_new",
            "is_coming_soon",
            "in_stock",
            "has_variant_price",
            "has_price_options",
            "created_at",
        )


class ProductDetailSerializer(serializers.ModelSerializer):
    display_name = serializers.CharField(read_only=True)
    display_short_description = serializers.CharField(read_only=True)
    display_description = serializers.CharField(read_only=True)
    display_specifications_text = serializers.CharField(read_only=True)
    display_warranty_text = serializers.CharField(read_only=True)
    display_meta_title = serializers.CharField(read_only=True)
    display_meta_description = serializers.CharField(read_only=True)
    discount_percentage = serializers.IntegerField(read_only=True)
    in_stock = serializers.BooleanField(read_only=True)
    has_variant_price = serializers.BooleanField(read_only=True)
    has_price_options = serializers.BooleanField(read_only=True)

    category = CategoryMinimalSerializer(read_only=True)
    images = ProductImageSerializer(many=True, read_only=True)
    specifications = ProductSpecificationSerializer(many=True, read_only=True)
    variants = serializers.SerializerMethodField()
    related_products = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = (
            "id",
            "name",
            "name_ar",
            "slug",
            "sku",
            "category",
            "short_description",
            "short_description_ar",
            "description",
            "description_ar",
            "specifications_text",
            "specifications_text_ar",
            "warranty_text",
            "warranty_text_ar",
            "price",
            "old_price",
            "discount_percentage",
            "main_image",
            "is_featured",
            "is_best_seller",
            "is_new",
            "is_coming_soon",
            "in_stock",
            "stock_quantity",
            "has_variant_price",
            "has_price_options",
            "display_name",
            "display_short_description",
            "display_description",
            "display_specifications_text",
            "display_warranty_text",
            "display_meta_title",
            "display_meta_description",
            "meta_title",
            "meta_title_ar",
            "meta_description",
            "meta_description_ar",
            "images",
            "specifications",
            "variants",
            "related_products",
            "created_at",
            "updated_at",
        )

    @extend_schema_field(ProductVariantSerializer(many=True))
    def get_variants(self, obj):
        active_variants = obj.variants.filter(is_active=True)
        return ProductVariantSerializer(active_variants, many=True, context=self.context).data

    @extend_schema_field(ProductListSerializer(many=True))
    def get_related_products(self, obj):
        related = Product.objects.filter(
            category=obj.category,
            is_active=True,
            category__is_active=True,
        ).exclude(pk=obj.pk).select_related("category").prefetch_related("variants")[:4]
        return ProductListSerializer(related, many=True, context=self.context).data


class HomepagePlacementSerializer(serializers.ModelSerializer):
    product = ProductListSerializer(read_only=True)

    class Meta:
        model = HomepageProduct
        fields = ("id", "product", "sort_order", "is_active")


class HomepageResponseSerializer(serializers.Serializer):
    hero_banner = serializers.DictField(allow_null=True)
    featured_products = ProductListSerializer(many=True)

