from django.test import TestCase
from django.urls import reverse
from .models import Category, Product, ProductVariant


class CatalogTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.category = Category.objects.create(name="Lighting", slug="lights")
        cls.product = Product.objects.create(name="Test Lamp", slug="test-lamp", sku="TEST-1", category=cls.category, short_description="A reliable lamp", description="Product description", price=100, old_price=125, stock_quantity=4, is_active=True)

    def test_product_detail(self):
        response = self.client.get(self.product.get_absolute_url())
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Test Lamp")

    def test_filter_by_category(self):
        response = self.client.get(reverse("catalog:list"), {"category": "lights"})
        self.assertContains(response, "Test Lamp")

    def test_search_suggestions(self):
        response = self.client.get(reverse("catalog:suggestions"), {"q": "Lamp"})
        self.assertEqual(response.json()["results"][0]["name"], "Test Lamp")

    def test_available_filter_includes_product_with_stocked_variant(self):
        product = Product.objects.create(
            name="Switch with Variants", slug="variant-switch", sku="SW-BASE", category=self.category,
            short_description="Multiple options", description="Product description", price=120, stock_quantity=0,
        )
        ProductVariant.objects.create(product=product, sku="SW-WHITE", label="White", stock_quantity=3)
        response = self.client.get(reverse("catalog:list"), {"available": "1"})
        self.assertContains(response, "Switch with Variants")
