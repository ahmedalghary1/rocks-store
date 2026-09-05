from io import BytesIO
from tempfile import TemporaryDirectory

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.test import override_settings
from django.urls import reverse
from PIL import Image
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


class ProductImageProcessingTests(TestCase):
    def setUp(self):
        self.category = Category.objects.create(name="Charging Cables", slug="charging-cables")

    @staticmethod
    def uploaded_image(name, image_format="JPEG", size=(3200, 1800), mode="RGB"):
        content = BytesIO()
        color = (18, 180, 60, 120) if mode == "RGBA" else (18, 180, 60)
        Image.new(mode, size, color).save(content, format=image_format)
        return SimpleUploadedFile(name, content.getvalue(), content_type=f"image/{image_format.lower()}")

    def test_product_image_keeps_dimensions_as_webp_and_old_files_are_removed(self):
        with TemporaryDirectory() as media_root, override_settings(MEDIA_ROOT=media_root):
            product = Product.objects.create(
                name="Type 2 Cable",
                slug="type-2-cable",
                sku="TYPE2-TEST",
                category=self.category,
                short_description="Test cable",
                description="Test cable description",
                price=100,
                stock_quantity=1,
                main_image=self.uploaded_image("original.jpg"),
            )

            self.assertTrue(product.main_image.name.endswith(".webp"))
            first_name = product.main_image.name
            self.assertTrue(product.main_image.storage.exists(first_name))
            with product.main_image.open("rb") as saved_image:
                with Image.open(saved_image) as image:
                    self.assertEqual(image.format, "WEBP")
                    self.assertEqual(image.size, (3200, 1800))

            product.main_image = self.uploaded_image("replacement.png", "PNG", (900, 900), "RGBA")
            product.save(update_fields=("main_image",))
            self.assertFalse(product.main_image.storage.exists(first_name))
            self.assertTrue(product.main_image.name.endswith("replacement.webp"))

            replacement_name = product.main_image.name
            product.delete()
            self.assertFalse(product.main_image.storage.exists(replacement_name))
