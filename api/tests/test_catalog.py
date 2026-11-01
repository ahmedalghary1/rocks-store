from decimal import Decimal
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from catalog.models import Category, HomepageProduct, Product, ProductVariant
from marketing.models import Banner


class CatalogAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.category = Category.objects.create(
            name="Chargers",
            name_ar="شواحن",
            slug="chargers",
            is_active=True,
            sort_order=1,
        )
        self.inactive_category = Category.objects.create(
            name="Inactive Cat",
            name_ar="تصنيف غير نشط",
            slug="inactive-cat",
            is_active=False,
        )

        self.product1 = Product.objects.create(
            name="ROCKS Wallbox 22kW",
            name_ar="شاحن روكس جداري 22 كيلو واط",
            slug="rocks-wallbox-22kw",
            sku="RK-WB-22",
            category=self.category,
            short_description="Smart 22kW EV charger",
            description="Full product description for Wallbox 22kW",
            price=Decimal("18500.00"),
            old_price=Decimal("20000.00"),
            stock_quantity=10,
            is_active=True,
            is_featured=True,
        )

        self.product2 = Product.objects.create(
            name="Type 2 Cable 5m",
            name_ar="كابل شحن 5 متر",
            slug="type-2-cable-5m",
            sku="RK-CBL-5M",
            category=self.category,
            short_description="5m charging cable",
            description="Full product description for 5m cable",
            price=Decimal("4500.00"),
            stock_quantity=0,
            is_active=True,
        )

        self.variant = ProductVariant.objects.create(
            product=self.product2,
            sku="RK-CBL-5M-16A",
            label="16A Single Phase",
            label_ar="16 أمبير أحادي الطور",
            price=Decimal("4200.00"),
            stock_quantity=5,
            is_active=True,
        )

        self.homepage_product = HomepageProduct.objects.create(
            product=self.product1,
            sort_order=1,
            is_active=True,
        )

        self.banner = Banner.objects.create(
            title="Summer EV Sale",
            title_ar="عروض الصيف",
            location="hero",
            is_active=True,
        )

    def test_category_list_and_detail(self):
        url = reverse("api:category-list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Should contain active category with products count = 2
        categories = response.data["results"] if "results" in response.data else response.data
        self.assertEqual(len(categories), 1)
        self.assertEqual(categories[0]["slug"], "chargers")
        self.assertEqual(categories[0]["products_count"], 2)

        # Retrieve detail
        detail_url = reverse("api:category-detail", kwargs={"slug": "chargers"})
        detail_res = self.client.get(detail_url)
        self.assertEqual(detail_res.status_code, status.HTTP_200_OK)
        self.assertEqual(detail_res.data["name"], "Chargers")

    def test_category_localization_header(self):
        detail_url = reverse("api:category-detail", kwargs={"slug": "chargers"})
        response = self.client.get(detail_url, HTTP_ACCEPT_LANGUAGE="ar")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["display_name"], "شواحن")

    def test_product_list_and_filtering(self):
        url = reverse("api:product-list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 2)

        # Filter by is_featured
        res_featured = self.client.get(url, {"is_featured": "true"})
        self.assertEqual(res_featured.data["count"], 1)
        self.assertEqual(res_featured.data["results"][0]["slug"], "rocks-wallbox-22kw")

        # Filter by price
        res_price = self.client.get(url, {"min_price": "10000"})
        self.assertEqual(res_price.data["count"], 1)

        # Filter by category
        res_cat = self.client.get(url, {"category": "chargers"})
        self.assertEqual(res_cat.data["count"], 2)

        # Search query
        res_search = self.client.get(url, {"search": "wallbox"})
        self.assertEqual(res_search.data["count"], 1)

    def test_product_detail(self):
        url = reverse("api:product-detail", kwargs={"slug": "type-2-cable-5m"})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["sku"], "RK-CBL-5M")
        self.assertEqual(len(response.data["variants"]), 1)
        self.assertEqual(response.data["variants"][0]["sku"], "RK-CBL-5M-16A")
        self.assertEqual(len(response.data["related_products"]), 1)

    def test_product_autocomplete_suggestions(self):
        url = reverse("api:product-suggest")
        res = self.client.get(url, {"q": "Wallbox"})
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data["results"]), 1)
        self.assertEqual(res.data["results"][0]["name"], "ROCKS Wallbox 22kW")

    def test_homepage_view(self):
        url = reverse("api:catalog-homepage")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("hero_banner", response.data)
        self.assertIn("featured_products", response.data)
        self.assertEqual(response.data["hero_banner"]["title"], "Summer EV Sale")
        self.assertTrue(len(response.data["featured_products"]) >= 1)

