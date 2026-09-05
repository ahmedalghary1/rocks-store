from django.core.management import call_command
from django.core.management.base import CommandError
from django.core.cache import cache
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from marketing.models import Subscriber
from .models import ContactMessage


class PublicPagesTests(TestCase):
    def setUp(self):
        cache.clear()

    def test_language_switch_renders_complete_arabic_shell(self):
        response = self.client.post(reverse("set_language"), {"language": "ar", "next": reverse("core:home")})
        self.assertRedirects(response, reverse("core:home"))
        response = self.client.get(reverse("core:home"))
        self.assertContains(response, '<html lang="ar" dir="rtl">', html=False)
        self.assertContains(response, "حلول شحن السيارات الكهربائية")
        self.assertContains(response, "English")
        self.assertContains(response, "hero-ev-ar-desktop.webp")
        self.assertContains(response, "hero-ev-ar-mobile.webp")
        self.assertNotContains(response, "hero-ev-en-desktop.webp")

        self.client.post(reverse("set_language"), {"language": "en", "next": reverse("core:home")})
        response = self.client.get(reverse("core:home"))
        self.assertContains(response, '<html lang="en" dir="ltr">', html=False)
        self.assertContains(response, "EV CHARGING SOLUTIONS")
        self.assertContains(response, "hero-ev-en-desktop.webp")
        self.assertContains(response, "hero-ev-en-mobile.webp")
        self.assertNotContains(response, "hero-ev-ar-desktop.webp")

    def test_health_and_legal_pages(self):
        self.assertEqual(self.client.get(reverse("core:health")).status_code, 200)
        for name in ("privacy", "terms", "shipping_policy", "returns_policy"):
            self.assertEqual(self.client.get(reverse(f"core:{name}")).status_code, 200)

    def test_contact_validates_on_server(self):
        response = self.client.post(reverse("core:contact"), {
            "name": "Test User", "phone": "bad", "email": "bad", "subject": "Question", "message": "Message",
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(ContactMessage.objects.count(), 0)

    def test_newsletter_subscription(self):
        response = self.client.post(reverse("core:newsletter_subscribe"), {"email": "USER@example.com"})
        self.assertRedirects(response, reverse("core:home"))
        self.assertTrue(Subscriber.objects.filter(email="user@example.com", is_active=True).exists())

    def test_production_readiness_rejects_incomplete_business_data(self):
        with self.assertRaises(CommandError):
            call_command("check_production_readiness")


class ArabicManagementDashboardTests(TestCase):
    def setUp(self):
        self.admin_user = get_user_model().objects.create_superuser(
            username="dashboard-admin",
            email="admin@example.com",
            password="Strong-test-password-982!",
        )

    def test_dashboard_is_staff_only_and_renders_arabic_overview(self):
        response = self.client.get(reverse("rocks_admin:index"))
        self.assertEqual(response.status_code, 302)

        self.client.force_login(self.admin_user)
        response = self.client.get(reverse("rocks_admin:index"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "نظرة عامة على المتجر")
        self.assertContains(response, "المنتجات والمخزون")
        self.assertContains(response, "admin-rocks.css")
        self.assertContains(response, "admin-rocks.js")
        self.assertContains(response, 'id="toggle-nav-sidebar"')

    def test_catalog_management_is_arabic_while_storefront_stays_english(self):
        self.client.force_login(self.admin_user)
        dashboard_response = self.client.get(reverse("rocks_admin:catalog_product_changelist"))
        self.assertEqual(dashboard_response.status_code, 200)
        self.assertContains(dashboard_response, "المنتجات")

        add_response = self.client.get(reverse("rocks_admin:catalog_product_add"))
        self.assertEqual(add_response.status_code, 200)
        self.assertContains(add_response, "السعر")
        self.assertContains(add_response, 'lang="ar"', html=False)

        storefront_response = self.client.get(reverse("core:home"))
        self.assertContains(storefront_response, '<html lang="en" dir="ltr">', html=False)

    def test_limited_staff_cannot_see_restricted_dashboard_data(self):
        limited_staff = get_user_model().objects.create_user(username="limited", password="Strong-password-981!", is_staff=True)
        self.client.force_login(limited_staff)
        response = self.client.get(reverse("rocks_admin:index"))
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "أحدث الطلبات")
        self.assertNotContains(response, "منتجات أوشكت على النفاد")
