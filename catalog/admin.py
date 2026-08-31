from django.contrib import admin
from django.utils.html import format_html
from .models import Category, Product, ProductAttribute, ProductImage, ProductSpecification, ProductVariant


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 0


class ProductSpecificationInline(admin.TabularInline):
    model = ProductSpecification
    extra = 1


class ProductVariantInline(admin.TabularInline):
    model = ProductVariant
    extra = 0


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "parent", "is_active", "sort_order")
    list_filter = ("is_active",)
    search_fields = ("name", "description")
    prepopulated_fields = {"slug": ("name",)}


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("name", "sku", "category", "price", "stock_quantity", "is_active", "thumbnail")
    list_filter = ("category", "is_active", "is_featured", "is_best_seller", "is_new")
    search_fields = ("name", "sku", "description")
    prepopulated_fields = {"slug": ("name",)}
    autocomplete_fields = ("category",)
    inlines = (ProductImageInline, ProductSpecificationInline, ProductVariantInline)

    @admin.display(description="الصورة")
    def thumbnail(self, obj):
        return format_html('<img src="{}" width="44" height="44" style="object-fit:contain">', obj.main_image.url) if obj.main_image else "—"


admin.site.register(ProductAttribute)
