from django.test import TestCase
from django.urls import reverse
from catalog.models import Category, Product, ProductVariant
from orders.models import Coupon
from django.utils import timezone
from datetime import timedelta


class CartTests(TestCase):
    def setUp(self):
        category = Category.objects.create(name="Tools", slug="tools")
        self.product = Product.objects.create(name="Voltage Tester", slug="tester", sku="T-1", category=category, short_description="Safe", description="Product description", price=120, stock_quantity=3)

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

    def test_zero_stock_product_is_not_added(self):
        self.product.stock_quantity = 0
        self.product.save(update_fields=("stock_quantity",))
        response = self.client.post(reverse("cart:add", args=[self.product.id]), {"quantity": 1})
        self.assertRedirects(response, reverse("cart:detail"))
        self.assertEqual(self.client.session.get("cart", {}), {})

    def test_variant_has_independent_stock(self):
        variant = ProductVariant.objects.create(product=self.product, sku="T-1-B", label="Large", price=175, stock_quantity=2)
        self.client.post(reverse("cart:add", args=[self.product.id]), {"quantity": 5, "variant_id": variant.id})
        self.assertEqual(self.client.session["cart"][f"{self.product.id}:{variant.id}"], 2)

    def test_external_next_url_is_rejected(self):
        response = self.client.post(reverse("cart:add", args=[self.product.id]), {"quantity": 1, "next": "https://evil.example/"})
        self.assertRedirects(response, reverse("cart:detail"))

    def test_corrupt_session_cart_is_recovered_without_server_error(self):
        session = self.client.session
        session["cart"] = {str(self.product.id): "not-a-number", "broken:key": 2}
        session.save()

        response = self.client.get(reverse("cart:detail"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.client.session["cart"], {})

    def test_ajax_quantity_update_recalculates_line_and_cart_totals(self):
        self.client.post(reverse("cart:add", args=[self.product.id]), {"quantity": 1})

        response = self.client.post(
            reverse("cart:update", args=[str(self.product.id)]),
            {"quantity": 3},
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["quantity"], 3)
        self.assertEqual(payload["count"], 3)
        self.assertEqual(payload["item_total"], "360.00")
        self.assertEqual(payload["subtotal"], "360.00")
        self.assertEqual(self.client.session["cart"][str(self.product.id)], 3)

    def test_mobile_add_button_submits_the_main_quantity_form(self):
        response = self.client.get(self.product.get_absolute_url())

        self.assertContains(response, 'form="detail-cart-form"', count=1)
