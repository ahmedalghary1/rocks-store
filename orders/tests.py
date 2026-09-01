from django.test import TestCase
from django.urls import reverse
from catalog.models import Category, Product
from .models import Order
from .services import restore_order_stock


class CheckoutTests(TestCase):
    def setUp(self):
        category = Category.objects.create(name="إضاءة", slug="lighting")
        self.product = Product.objects.create(name="لمبة 12 وات", slug="lamp-12", sku="L-12", category=category, short_description="موفرة", description="وصف", price=95, stock_quantity=5)

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
        self.assertContains(checkout_page, "190,00")
        token = self.client.session["checkout_token"]
        response = self.client.post(reverse("orders:checkout"), {"checkout_token":token, "customer_name":"محمد أحمد", "phone":"01012345678", "email":"", "second_phone":"", "governorate":"القاهرة", "city":"مدينة نصر", "address":"١ شارع الطاقة", "notes":"", "payment_method":"cod"})
        self.assertEqual(response.status_code, 302)
        order = Order.objects.get()
        item = order.items.get()
        self.assertEqual(item.product_name, "لمبة 12 وات")
        self.assertEqual(item.quantity, 2)
        self.assertEqual(item.price, 95)
        self.assertEqual(item.total, 190)
        self.assertEqual(order.subtotal, 190)
        success = self.client.get(response.url)
        self.assertContains(success, "2×")
        self.assertContains(success, "190,00")
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock_quantity, 3)
        self.assertIn(str(order.public_token), response.url)

    def test_empty_cart_redirects(self):
        response = self.client.get(reverse("orders:checkout"))
        self.assertRedirects(response, reverse("catalog:list"))

    def test_same_checkout_token_cannot_create_duplicate_order(self):
        self.client.post(reverse("cart:add", args=[self.product.id]), {"quantity": 1})
        self.client.get(reverse("orders:checkout"))
        token = self.client.session["checkout_token"]
        payload = {"checkout_token":token, "customer_name":"محمد", "phone":"01012345678", "email":"", "second_phone":"", "governorate":"القاهرة", "city":"القاهرة", "address":"شارع الاختبار", "notes":"", "payment_method":"cod"}
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
        self.client.post(reverse("orders:checkout"), {"checkout_token":token, "customer_name":"محمد", "phone":"01012345678", "email":"", "second_phone":"", "governorate":"القاهرة", "city":"القاهرة", "address":"شارع الاختبار", "notes":"", "payment_method":"cod"})
        order = Order.objects.get()
        self.assertTrue(restore_order_stock(order.pk))
        self.assertFalse(restore_order_stock(order.pk))
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock_quantity, 5)
