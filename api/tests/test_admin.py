from decimal import Decimal
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from catalog.models import Category, Product
from core.models import ContactMessage
from orders.models import Order, OrderItem

User = get_user_model()


class AdminAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.staff_user = User.objects.create_user(username="adminuser", password="AdminPassword123!", is_staff=True)
        self.regular_user = User.objects.create_user(username="normaluser", password="NormalPassword123!", is_staff=False)

        self.category = Category.objects.create(name="Chargers", slug="chargers", is_active=True)
        self.product = Product.objects.create(
            name="Commercial Charger 44kW",
            slug="commercial-charger-44kw",
            sku="RK-COMM-44",
            category=self.category,
            short_description="44kW Dual",
            description="Commercial charger",
            price=Decimal("45000.00"),
            stock_quantity=3,
            is_active=True,
        )

        self.order = Order.objects.create(
            order_number="RK-261101-TEST1234",
            customer_name="Company ABC",
            phone="01012345678",
            governorate="Giza",
            city="6th of October",
            address="Industrial Zone",
            subtotal=Decimal("45000.00"),
            shipping_cost=Decimal("0.00"),
            discount=Decimal("0.00"),
            total=Decimal("45000.00"),
            payment_method="cod",
            payment_status="unpaid",
            status="pending",
        )
        self.order_item = OrderItem.objects.create(
            order=self.order,
            product=self.product,
            product_name=self.product.name,
            sku=self.product.sku,
            price=Decimal("45000.00"),
            quantity=1,
            total=Decimal("45000.00"),
        )

        self.contact_msg = ContactMessage.objects.create(
            name="Prospect",
            phone="01234567890",
            subject="Bulk order",
            message="Need 10 chargers",
            is_read=False,
        )

    def test_permission_denied_for_regular_user(self):
        self.client.force_authenticate(user=self.regular_user)
        metrics_url = reverse("api:admin-metrics")
        res = self.client.get(metrics_url)
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_metrics(self):
        self.client.force_authenticate(user=self.staff_user)
        metrics_url = reverse("api:admin-metrics")
        res = self.client.get(metrics_url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["total_orders"], 1)
        self.assertEqual(res.data["pending_orders"], 1)
        self.assertEqual(Decimal(res.data["total_revenue"]), Decimal("45000.00"))
        self.assertEqual(res.data["unread_messages"], 1)

    def test_admin_order_status_update_and_inventory_restoration(self):
        self.client.force_authenticate(user=self.staff_user)
        update_url = reverse("api:admin-order-update-status", kwargs={"pk": self.order.pk})

        # 1. Update to confirmed
        res = self.client.patch(update_url, {"status": "confirmed", "payment_status": "unpaid"}, format="json")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, "confirmed")

        # Initial stock was 3
        self.assertEqual(self.product.stock_quantity, 3)

        # 2. Cancel order -> triggers automatic stock restoration!
        res_cancel = self.client.patch(update_url, {"status": "cancelled"}, format="json")
        self.assertEqual(res_cancel.status_code, status.HTTP_200_OK)
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, "cancelled")
        self.assertTrue(self.order.stock_restored)

        # Stock should now be restored by 1: 3 + 1 = 4
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock_quantity, 4)

        # 3. Cannot reopen cancelled order
        res_reopen = self.client.patch(update_url, {"status": "processing"}, format="json")
        self.assertEqual(res_reopen.status_code, status.HTTP_400_BAD_REQUEST)

    def test_admin_contact_message_mark_read(self):
        self.client.force_authenticate(user=self.staff_user)
        read_url = reverse("api:admin-contact-message-set-read", kwargs={"pk": self.contact_msg.pk})
        res = self.client.patch(read_url, {"is_read": True}, format="json")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.contact_msg.refresh_from_db()
        self.assertTrue(self.contact_msg.is_read)

