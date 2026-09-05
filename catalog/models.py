from decimal import Decimal
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import F, Q
from django.urls import reverse
from django.utils import translation
from .validators import validate_image_size
from core.image_processing import OptimizedImageFieldsMixin


def localized_value(instance, field_name):
    if translation.get_language() == "ar":
        return getattr(instance, f"{field_name}_ar", "") or getattr(instance, field_name)
    return getattr(instance, field_name)


class Category(OptimizedImageFieldsMixin, models.Model):
    optimized_image_fields = ("image",)
    name = models.CharField(max_length=120)
    name_ar = models.CharField("الاسم بالعربية", max_length=120, blank=True)
    slug = models.SlugField(unique=True, db_index=True)
    description = models.TextField(blank=True)
    description_ar = models.TextField("الوصف بالعربية", blank=True)
    image = models.ImageField(upload_to="categories/", blank=True, validators=[validate_image_size])
    icon = models.CharField(max_length=40, blank=True)
    parent = models.ForeignKey("self", null=True, blank=True, on_delete=models.PROTECT, related_name="children")
    is_active = models.BooleanField(default=True)
    sort_order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("sort_order", "name")
        indexes = [models.Index(fields=("is_active", "sort_order"))]
        verbose_name_plural = "Categories"

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return f"{reverse('catalog:list')}?category={self.slug}"

    @property
    def display_name(self):
        return localized_value(self, "name")

    @property
    def display_description(self):
        return localized_value(self, "description")


class Product(OptimizedImageFieldsMixin, models.Model):
    optimized_image_fields = ("main_image",)
    name = models.CharField(max_length=180)
    name_ar = models.CharField("الاسم بالعربية", max_length=180, blank=True)
    slug = models.SlugField(unique=True, db_index=True)
    sku = models.CharField(max_length=60, unique=True, db_index=True)
    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name="products")
    short_description = models.CharField(max_length=260)
    short_description_ar = models.CharField("الوصف المختصر بالعربية", max_length=260, blank=True)
    description = models.TextField()
    description_ar = models.TextField("الوصف بالعربية", blank=True)
    price = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(Decimal("0.01"))])
    old_price = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True, validators=[MinValueValidator(Decimal("0.01"))])
    main_image = models.ImageField(upload_to="products/", blank=True, validators=[validate_image_size])
    is_featured = models.BooleanField(default=False)
    is_best_seller = models.BooleanField(default=False)
    is_new = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    stock_quantity = models.PositiveIntegerField(default=0)
    meta_title = models.CharField(max_length=180, blank=True)
    meta_title_ar = models.CharField("عنوان محركات البحث بالعربية", max_length=180, blank=True)
    meta_description = models.CharField(max_length=260, blank=True)
    meta_description_ar = models.CharField("وصف محركات البحث بالعربية", max_length=260, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-created_at",)
        indexes = [models.Index(fields=("is_active", "category")), models.Index(fields=("is_active", "-created_at"))]
        constraints = [
            models.CheckConstraint(condition=Q(price__gt=0), name="product_price_positive"),
            models.CheckConstraint(condition=Q(old_price__isnull=True) | Q(old_price__gte=F("price")), name="product_old_price_valid"),
        ]

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("catalog:detail", kwargs={"slug": self.slug})

    @property
    def display_name(self):
        return localized_value(self, "name")

    @property
    def display_short_description(self):
        return localized_value(self, "short_description")

    @property
    def display_description(self):
        return localized_value(self, "description")

    @property
    def display_meta_title(self):
        return localized_value(self, "meta_title") or self.display_name

    @property
    def display_meta_description(self):
        return localized_value(self, "meta_description") or self.display_short_description

    @property
    def discount_percentage(self):
        if self.old_price and self.old_price > self.price:
            return int((self.old_price - self.price) / self.old_price * Decimal("100"))
        return 0

    @property
    def in_stock(self):
        prefetched = getattr(self, "_prefetched_objects_cache", {}).get("variants")
        if prefetched is not None and prefetched:
            return any(variant.is_active and variant.stock_quantity > 0 for variant in prefetched)
        if self.variants.filter(is_active=True).exists():
            return self.variants.filter(is_active=True, stock_quantity__gt=0).exists()
        return self.stock_quantity > 0


class ProductImage(OptimizedImageFieldsMixin, models.Model):
    optimized_image_fields = ("image",)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="images")
    image = models.ImageField(upload_to="products/gallery/", validators=[validate_image_size])
    alt_text = models.CharField(max_length=180)
    alt_text_ar = models.CharField("النص البديل بالعربية", max_length=180, blank=True)
    sort_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ("sort_order",)

    @property
    def display_alt_text(self):
        return localized_value(self, "alt_text")


class ProductSpecification(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="specifications")
    name = models.CharField(max_length=100)
    name_ar = models.CharField("اسم الخاصية بالعربية", max_length=100, blank=True)
    value = models.CharField(max_length=180)
    value_ar = models.CharField("القيمة بالعربية", max_length=180, blank=True)
    sort_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ("sort_order",)

    @property
    def display_name(self):
        return localized_value(self, "name")

    @property
    def display_value(self):
        return localized_value(self, "value")


class ProductAttribute(models.Model):
    name = models.CharField(max_length=80)
    name_ar = models.CharField("الاسم بالعربية", max_length=80, blank=True)
    slug = models.SlugField(unique=True)

    def __str__(self):
        return self.name

    @property
    def display_name(self):
        return localized_value(self, "name")


class ProductVariant(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="variants")
    sku = models.CharField(max_length=60, unique=True)
    label = models.CharField(max_length=120)
    label_ar = models.CharField("اسم الخيار بالعربية", max_length=120, blank=True)
    price = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True, validators=[MinValueValidator(Decimal("0.01"))])
    stock_quantity = models.PositiveIntegerField(default=0)
    attributes = models.JSONField(default=dict, blank=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.product.name} — {self.label}"

    @property
    def display_label(self):
        return localized_value(self, "label")

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=("product", "label"), name="unique_product_variant_label"),
            models.CheckConstraint(condition=Q(price__isnull=True) | Q(price__gt=0), name="variant_price_positive"),
        ]
