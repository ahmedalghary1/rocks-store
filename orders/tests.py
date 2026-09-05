from datetime import timedelta
from unittest.mock import patch

from django.core.cache import cache
from django.db.models.deletion import ProtectedError
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone
from catalog.models import Category, Product, ProductVariant
from .models import Coupon, Order, OrderNotification, ShippingZone
from .services import restore_order_stock, send_order_notifications


class CheckoutTests(TestCase):
    def setUp(self):
        cache.clear()
        category = Category.objects.create(name="Lighting", slug="lighting")
        self.product = Product.objects.create(name="12W Lamp", slug="lamp-12", sku="L-12", category=category, short_description="Energy efficient", description="Product description", price=95, stock_quantity=5)

    def checkout_payload(self, **overrides):
        payload = {"checkout_token": self.client.session["checkout_token"], "customer_name": "John Smith", "phone": "01012345678", "email": "", "second_phone": "", "governorate": "Cairo", "city": "Nasr City", "address": "1 Energy Street", "notes": ""}
        payload.update(overrides)
        return payload

    def test_checkout_creates_snapshot_and_decrements_stock(self):
        self.client.post(reverse("cart:add", args=[self.product.id]), {"quantity": 1})
        update_response = self.client.post(
            reverse("cart:update", args=[str(self.product.id)]),
            {"quantity": 2},
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        self.assertEqual(update_response.json()["subtotal"], "190.00")
        checkout_page = self.client.get(reverse("orders:checkout"))
        self.assertContains(checkout_page, "2×")
        self.assertContains(checkout_page, "190.00")
        token = self.client.session["checkout_token"]
        response = self.client.post(reverse("orders:checkout"), {"checkout_token":token, "customer_name":"John Smith", "phone":"01012345678", "email":"", "second_phone":"", "governorate":"Cairo", "city":"Nasr City", "address":"1 Energy Street", "notes":"", "payment_method":"cod"})
        self.assertEqual(response.status_code, 302)
        order = Order.objects.get()
        item = order.items.get()
        self.assertEqual(item.product_name, "12W Lamp")
        self.assertEqual(item.quantity, 2)
        self.assertEqual(item.price, 95)
        self.assertEqual(item.total, 190)
        self.assertEqual(order.subtotal, 190)
        success = self.client.get(response.url)
        self.assertContains(success, "2×")
        self.assertContains(success, "190.00")
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock_quantity, 3)
        self.assertIn(str(order.public_token), response.url)
        self.assertEqual(order.payment_method, "cod")
        self.assertEqual(order.notification.status, "pending")

    def test_empty_cart_redirects(self):
        response = self.client.get(reverse("orders:checkout"))
        self.assertRedirects(response, reverse("catalog:list"))

    def test_same_checkout_token_cannot_create_duplicate_order(self):
        self.client.post(reverse("cart:add", args=[self.product.id]), {"quantity": 1})
        self.client.get(reverse("orders:checkout"))
        token = self.client.session["checkout_token"]
        payload = {"checkout_token":token, "customer_name":"John", "phone":"01012345678", "email":"", "second_phone":"", "governorate":"Cairo", "city":"Cairo", "address":"Test Street", "notes":"", "payment_method":"cod"}
        self.client.post(reverse("orders:checkout"), payload)
        session = self.client.session
        session["cart"] = {str(self.product.id): 1}
        session["checkout_token"] = token
        session.save()
        self.client.post(reverse("orders:checkout"), payload)
        self.assertEqual(Order.objects.count(), 1)
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock_quantity, 4)

    def test_stock_restore_is_idempotent(self):
        self.client.post(reverse("cart:add", args=[self.product.id]), {"quantity": 2})
        self.client.get(reverse("orders:checkout"))
        token = self.client.session["checkout_token"]
        self.client.post(reverse("orders:checkout"), {"checkout_token":token, "customer_name":"John", "phone":"01012345678", "email":"", "second_phone":"", "governorate":"Cairo", "city":"Cairo", "address":"Test Street", "notes":"", "payment_method":"cod"})
        order = Order.objects.get()
        self.assertTrue(restore_order_stock(order.pk))
        self.assertFalse(restore_order_stock(order.pk))
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock_quantity, 5)

    def test_posted_payment_method_is_ignored_and_cod_is_saved(self):
        self.client.post(reverse("cart:add", args=[self.product.id]), {"quantity": 1})
        self.client.get(reverse("orders:checkout"))
        response = self.client.post(reverse("orders:checkout"), self.checkout_payload(payment_method="bank"))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Order.objects.get().payment_method, "cod")

    def test_shipping_zone_controls_final_shipping_cost(self):
        ShippingZone.objects.filter(name="Cairo").update(shipping_cost=123, free_shipping_threshold=None)
        self.client.post(reverse("cart:add", args=[self.product.id]), {"quantity": 1})
        self.client.get(reverse("orders:checkout"))
        self.client.post(reverse("orders:checkout"), self.checkout_payload())
        order = Order.objects.get()
        self.assertEqual(order.shipping_cost, 123)
        self.assertEqual(order.total, 218)

    def test_variant_referenced_by_order_cannot_be_deleted(self):
        variant = ProductVariant.objects.create(product=self.product, sku="L-12-W", label="White", stock_quantity=2)
        self.client.post(reverse("cart:add", args=[self.product.id]), {"quantity": 1, "variant_id": variant.id})
        self.client.get(reverse("orders:checkout"))
        self.client.post(reverse("orders:checkout"), self.checkout_payload())
        with self.assertRaises(ProtectedError):
            variant.delete()

    @override_settings(ORDER_NOTIFICATION_EMAIL="orders@example.com")
    def test_failed_notification_is_persisted_and_can_be_retried(self):
        self.client.post(reverse("cart:add", args=[self.product.id]), {"quantity": 1})
        self.client.get(reverse("orders:checkout"))
        self.client.post(reverse("orders:checkout"), self.checkout_payload())
        order = Order.objects.get()
        with patch("orders.services.send_mail", side_effect=OSError("SMTP unavailable")):
            self.assertFalse(send_order_notifications(order.pk))
        notification = OrderNotification.objects.get(order=order)
        self.assertEqual(notification.status, "failed")
        self.assertEqual(notification.attempts, 1)
        with patch("orders.services.send_mail", return_value=1):
            self.assertTrue(send_order_notifications(order.pk))
        notification.refresh_from_db()
        self.assertEqual(notification.status, "sent")
        self.assertEqual(notification.attempts, 2)

    def test_cancelled_order_restores_coupon_usage_once(self):
        coupon = Coupon.objects.create(code="SAVE", discount_type="fixed", value=10, start_date=timezone.now() - timedelta(days=1), end_date=timezone.now() + timedelta(days=1))
        self.client.post(reverse("cart:add", args=[self.product.id]), {"quantity": 1})
        self.client.post(reverse("cart:apply_coupon"), {"code": coupon.code})
        self.client.get(reverse("orders:checkout"))
        self.client.post(reverse("orders:checkout"), self.checkout_payload())
        order = Order.objects.get()
        coupon.refresh_from_db()
        self.assertEqual(coupon.usage_count, 1)
        self.assertTrue(restore_order_stock(order.pk))
        coupon.refresh_from_db()
        self.assertEqual(coupon.usage_count, 0)

    def test_guest_can_track_order_with_number_and_phone(self):
        self.client.post(reverse("cart:add", args=[self.product.id]), {"quantity": 1})
        self.client.get(reverse("orders:checkout"))
        self.client.post(reverse("orders:checkout"), self.checkout_payload())
        order = Order.objects.get()
        session = self.client.session
        session.pop("last_order_token", None)
        session.save()
        response = self.client.post(reverse("orders:track"), {"order_number": order.order_number, "phone": order.phone})
        self.assertRedirects(response, reverse("orders:success", args=[order.public_token]))
