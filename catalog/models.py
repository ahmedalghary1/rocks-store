from decimal import Decimal
from django.db import models
from django.urls import reverse


class Category(models.Model):
    name = models.CharField(max_length=120)
    slug = models.SlugField(unique=True, db_index=True)
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to="categories/", blank=True)
    icon = models.CharField(max_length=40, blank=True)
    parent = models.ForeignKey("self", null=True, blank=True, on_delete=models.PROTECT, related_name="children")
    is_active = models.BooleanField(default=True)
    sort_order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("sort_order", "name")
        indexes = [models.Index(fields=("is_active", "sort_order"))]
        verbose_name_plural = "التصنيفات"

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return f"{reverse('catalog:list')}?category={self.slug}"


class Product(models.Model):
    name = models.CharField(max_length=180)
    slug = models.SlugField(unique=True, db_index=True)
    sku = models.CharField(max_length=60, unique=True, db_index=True)
    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name="products")
    short_description = models.CharField(max_length=260)
    description = models.TextField()
    price = models.DecimalField(max_digits=12, decimal_places=2)
    old_price = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    main_image = models.ImageField(upload_to="products/", blank=True)
    is_featured = models.BooleanField(default=False)
    is_best_seller = models.BooleanField(default=False)
    is_new = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    stock_quantity = models.PositiveIntegerField(default=0)
    meta_title = models.CharField(max_length=180, blank=True)
    meta_description = models.CharField(max_length=260, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-created_at",)
        indexes = [models.Index(fields=("is_active", "category")), models.Index(fields=("is_active", "-created_at"))]

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("catalog:detail", kwargs={"slug": self.slug})

    @property
    def discount_percentage(self):
        if self.old_price and self.old_price > self.price:
            return int((self.old_price - self.price) / self.old_price * Decimal("100"))
        return 0

    @property
    def in_stock(self):
        return self.stock_quantity > 0


class ProductImage(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="images")
    image = models.ImageField(upload_to="products/gallery/")
    alt_text = models.CharField(max_length=180)
    sort_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ("sort_order",)


class ProductSpecification(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="specifications")
    name = models.CharField(max_length=100)
    value = models.CharField(max_length=180)
    sort_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ("sort_order",)


class ProductAttribute(models.Model):
    name = models.CharField(max_length=80)
    slug = models.SlugField(unique=True)

    def __str__(self):
        return self.name


class ProductVariant(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="variants")
    sku = models.CharField(max_length=60, unique=True)
    label = models.CharField(max_length=120)
    price = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    stock_quantity = models.PositiveIntegerField(default=0)
    attributes = models.JSONField(default=dict, blank=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.product.name} — {self.label}"
