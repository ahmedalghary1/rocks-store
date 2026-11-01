from datetime import timedelta
from decimal import Decimal
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from catalog.models import Category, Product, ProductVariant
from orders.models import Coupon


class CartAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.category = Category.objects.create(name="Chargers", slug="chargers", is_active=True)
        self.product = Product.objects.create(
            name="ROCKS Wallbox 7kW",
            slug="rocks-wallbox-7kw",
            sku="RK-WB-7",
            category=self.category,
            short_description="7kW EV charger",
            description="7kW EV charger details",
            price=Decimal("12000.00"),
            stock_quantity=5,
            is_active=True,
        )
        self.product_with_variants = Product.objects.create(
            name="Cable",
            slug="cable",
            sku="RK-CBL",
            category=self.category,
            short_description="Cable",
            description="Cable details",
            stock_quantity=0,
            is_active=True,
        )
        self.variant = ProductVariant.objects.create(
            product=self.product_with_variants,
            sku="RK-CBL-7M",
            label="7 Meters",
            price=Decimal("3500.00"),
            stock_quantity=4,
            is_active=True,
        )

        now = timezone.now()
        self.coupon = Coupon.objects.create(
            code="ROCKS10",
            discount_type="percentage",
            value=Decimal("10.00"),
            minimum_order=Decimal("1000.00"),
            start_date=now - timedelta(days=1),
            end_date=now + timedelta(days=10),
            usage_limit=50,
            usage_count=0,
            is_active=True,
        )

    def test_cart_workflow(self):
        cart_url = reverse("api:cart-detail")
        items_url = reverse("api:cart-items")

        # 1. Initially empty
        res = self.client.get(cart_url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["count"], 0)
        self.assertEqual(len(res.data["items"]), 0)

        # 2. Add product without variant
        add_res = self.client.post(items_url, {"product_id": self.product.id, "quantity": 2}, format="json")
        self.assertEqual(add_res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(add_res.data["count"], 2)
        self.assertEqual(len(add_res.data["items"]), 1)
        item_key = add_res.data["items"][0]["key"]

        # 3. Add product with variant
        add_var_res = self.client.post(
            items_url,
            {"product_id": self.product_with_variants.id, "variant_id": self.variant.id, "quantity": 1},
            format="json",
        )
        self.assertEqual(add_var_res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(add_var_res.data["count"], 3)
        self.assertEqual(len(add_var_res.data["items"]), 2)

        # 4. Update quantity
        update_url = reverse("api:cart-item-detail", kwargs={"item_key": item_key})
        update_res = self.client.patch(update_url, {"quantity": 1}, format="json")
        self.assertEqual(update_res.status_code, status.HTTP_200_OK)
        self.assertEqual(update_res.data["count"], 2)

        # 5. Apply Coupon
        coupon_url = reverse("api:cart-coupon")
        coupon_res = self.client.post(coupon_url, {"code": "ROCKS10"}, format="json")
        self.assertEqual(coupon_res.status_code, status.HTTP_200_OK)
        self.assertIsNotNone(coupon_res.data["coupon"])
        self.assertEqual(coupon_res.data["coupon"]["code"], "ROCKS10")
        self.assertTrue(Decimal(coupon_res.data["discount"]) > 0)

        # 6. Remove Coupon
        rm_coupon_res = self.client.delete(coupon_url)
        self.assertEqual(rm_coupon_res.status_code, status.HTTP_200_OK)
        self.assertIsNone(rm_coupon_res.data["coupon"])

        # 7. Delete Item
        del_res = self.client.delete(update_url)
        self.assertEqual(del_res.status_code, status.HTTP_200_OK)
        self.assertEqual(del_res.data["count"], 1)

        # 8. Clear Cart
        clear_url = reverse("api:cart-clear")
        clear_res = self.client.post(clear_url)
        self.assertEqual(clear_res.status_code, status.HTTP_200_OK)
        self.assertEqual(clear_res.data["count"], 0)
        self.assertEqual(len(clear_res.data["items"]), 0)

