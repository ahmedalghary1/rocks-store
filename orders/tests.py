from django.test import TestCase
from django.urls import reverse
from catalog.models import Category, Product
from .models import Order


class CheckoutTests(TestCase):
    def setUp(self):
        category = Category.objects.create(name="إضاءة", slug="lighting")
        self.product = Product.objects.create(name="لمبة 12 وات", slug="lamp-12", sku="L-12", category=category, short_description="موفرة", description="وصف", price=95, stock_quantity=5)

    def test_checkout_creates_snapshot_and_decrements_stock(self):
        self.client.post(reverse("cart:add", args=[self.product.id]), {"quantity": 2})
        response = self.client.post(reverse("orders:checkout"), {"customer_name":"محمد أحمد", "phone":"01012345678", "second_phone":"", "governorate":"القاهرة", "city":"مدينة نصر", "address":"١ شارع الطاقة", "notes":"", "payment_method":"cod"})
        self.assertEqual(response.status_code, 302)
        order = Order.objects.get()
        self.assertEqual(order.items.get().product_name, "لمبة 12 وات")
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock_quantity, 3)

    def test_empty_cart_redirects(self):
        response = self.client.get(reverse("orders:checkout"))
        self.assertRedirects(response, reverse("catalog:list"))
