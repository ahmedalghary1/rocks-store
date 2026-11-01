from datetime import timedelta
from decimal import Decimal
import uuid
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from catalog.models import Category, Product, ProductVariant
from orders.models import Coupon, Order, ShippingZone

User = get_user_model()


class OrdersAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username="customer", email="cust@example.com", password="Pass12345!")

        self.zone, _ = ShippingZone.objects.update_or_create(
            name="Cairo",
            defaults={
                "name_ar": "القاهرة",
                "shipping_cost": Decimal("60.00"),
                "free_shipping_threshold": Decimal("2000.00"),
                "is_active": True,
            },
        )

        self.category = Category.objects.create(name="Chargers", slug="chargers", is_active=True)
        self.product = Product.objects.create(
            name="Smart EV Charger 11kW",
            slug="smart-ev-charger-11kw",
            sku="RK-CH-11",
            category=self.category,
            short_description="Smart 11kW",
            description="Charger 11kW",
            price=Decimal("15000.00"),
            stock_quantity=8,
            is_active=True,
        )

        now = timezone.now()
        self.coupon = Coupon.objects.create(
            code="SAVE500",
            discount_type="fixed",
            value=Decimal("500.00"),
            minimum_order=Decimal("5000.00"),
            start_date=now - timedelta(days=1),
            end_date=now + timedelta(days=10),
            usage_limit=100,
            usage_count=0,
            is_active=True,
        )

    def test_shipping_zones_list(self):
        url = reverse("api:shipping-zones")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(len(response.data) >= 1)
        self.assertTrue(any(z["name"] == "Cairo" for z in response.data))

    def test_validate_coupon_endpoint(self):
        url = reverse("api:validate-coupon")
        # Valid case
        res = self.client.post(url, {"code": "SAVE500", "subtotal": "6000.00"}, format="json")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertTrue(res.data["valid"])
        self.assertEqual(Decimal(res.data["discount_amount"]), Decimal("500.00"))

        # Subtotal too low
        res_low = self.client.post(url, {"code": "SAVE500", "subtotal": "3000.00"}, format="json")
        self.assertEqual(res_low.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(res_low.data["valid"])

    def test_checkout_direct_payload_and_stock_deduction(self):
        url = reverse("api:checkout")
        idempotency_token = str(uuid.uuid4())
        payload = {
            "customer_name": "Kareem Hassan",
            "phone": "01009876543",
            "second_phone": "",
            "email": "kareem@example.com",
            "governorate": "Cairo",
            "city": "New Cairo",
            "address": "Street 90, Villa 12",
            "notes": "Call before delivery",
            "checkout_token": idempotency_token,
            "coupon_code": "SAVE500",
            "items": [
                {"product_id": self.product.id, "quantity": 2}
            ],
        }

        self.client.force_authenticate(user=self.user)
        response = self.client.post(url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn("order_number", response.data)
        self.assertEqual(response.data["customer_name"], "Kareem Hassan")
        self.assertEqual(Decimal(response.data["subtotal"]), Decimal("30000.00"))
        # subtotal >= 2000 => free shipping
        self.assertEqual(Decimal(response.data["shipping_cost"]), Decimal("0.00"))
        self.assertEqual(Decimal(response.data["discount"]), Decimal("500.00"))
        self.assertEqual(Decimal(response.data["total"]), Decimal("29500.00"))

        # Verify stock was deducted: 8 - 2 = 6
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock_quantity, 6)

        # Verify coupon usage was incremented
        self.coupon.refresh_from_db()
        self.assertEqual(self.coupon.usage_count, 1)

        # Verify idempotency retry
        retry_res = self.client.post(url, payload, format="json")
        self.assertEqual(retry_res.status_code, status.HTTP_200_OK)
        self.assertEqual(retry_res.data["order_number"], response.data["order_number"])

        self.client.force_authenticate(user=None)
        other_customer = dict(payload, customer_name="Someone Else")
        conflict = self.client.post(url, other_customer, format="json")
        self.assertEqual(conflict.status_code, status.HTTP_409_CONFLICT)

        bad_coupon = dict(payload, checkout_token=str(uuid.uuid4()), coupon_code="NOTREAL")
        invalid = self.client.post(url, bad_coupon, format="json")
        self.assertEqual(invalid.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Order.objects.count(), 1)

        # Test tracking endpoint
        track_url = reverse("api:order-track")
        track_res = self.client.post(track_url, {"order_number": response.data["order_number"], "phone": "01009876543"}, format="json")
        self.assertEqual(track_res.status_code, status.HTTP_200_OK)
        self.assertEqual(track_res.data["order_number"], response.data["order_number"])
        self.assertEqual(track_res.data["status"], "pending")

        # Test public receipt
        receipt_url = reverse("api:order-receipt", kwargs={"public_token": response.data["public_token"]})
        receipt_res = self.client.get(receipt_url)
        self.assertEqual(receipt_res.status_code, status.HTTP_200_OK)
        self.assertEqual(receipt_res.data["order_number"], response.data["order_number"])

        # Test customer order history
        self.client.force_authenticate(user=self.user)
        my_orders_url = reverse("api:user-order-list")
        my_orders_res = self.client.get(my_orders_url)
        self.assertEqual(my_orders_res.status_code, status.HTTP_200_OK)
        self.assertEqual(my_orders_res.data["count"], 1)
