from django.test import TestCase
from django.urls import reverse
from catalog.models import Category, Product
from orders.models import Coupon
from django.utils import timezone
from datetime import timedelta


class CartTests(TestCase):
    def setUp(self):
        category = Category.objects.create(name="أدوات", slug="tools")
        self.product = Product.objects.create(name="قلم فحص", slug="tester", sku="T-1", category=category, short_description="آمن", description="وصف", price=120, stock_quantity=3)

    def test_add_and_clamp_to_stock(self):
        self.client.post(reverse("cart:add", args=[self.product.id]), {"quantity": 8})
        self.assertEqual(self.client.session["cart"][str(self.product.id)], 3)

    def test_remove(self):
        self.client.post(reverse("cart:add", args=[self.product.id]), {"quantity": 1})
        self.client.post(reverse("cart:remove", args=[self.product.id]))
        self.assertNotIn(str(self.product.id), self.client.session["cart"])

    def test_valid_coupon_is_applied_server_side(self):
        Coupon.objects.create(code="SAVE10", discount_type="percentage", value=10, minimum_order=100, start_date=timezone.now()-timedelta(days=1), end_date=timezone.now()+timedelta(days=1), usage_limit=5)
        self.client.post(reverse("cart:add", args=[self.product.id]), {"quantity": 1})
        self.client.post(reverse("cart:apply_coupon"), {"code": "SAVE10"})
        self.assertEqual(self.client.session["coupon_code"], "SAVE10")
