from django.core.management import call_command
from django.core.management.base import CommandError
from django.core.cache import cache
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from marketing.models import Banner, Subscriber
from .models import ContactMessage


class PublicPagesTests(TestCase):
    def setUp(self):
        cache.clear()

    def test_language_switch_renders_complete_arabic_shell(self):
        from catalog.models import Category, Product

        category = Category.objects.create(name="Power Strips", slug="arabic-home-products")
        Product.objects.create(
            name="6-Outlet USB Power Strip",
            slug="arabic-home-product",
            sku="AR-HOME-1",
            category=category,
            short_description="Six outlets and two USB ports in one dependable power hub.",
            description="Test product",
            price=720,
            stock_quantity=5,
            is_featured=True,
        )
        response = self.client.post(reverse("set_language"), {"language": "ar", "next": reverse("core:home")})
        self.assertRedirects(response, reverse("core:home"))
        response = self.client.get(reverse("core:home"))
        self.assertContains(response, '<html lang="ar" dir="rtl">', html=False)
        self.assertContains(response, "حلول الكهرباء وشحن السيارات")
        self.assertContains(response, "لكل")
        self.assertContains(response, "توصيلة")
        self.assertContains(response, "التصنيفات الشائعة")
        self.assertContains(response, "مشترك كهربائي USB بـ 6 مخارج")
        self.assertContains(response, "ستة مخارج ومنفذا USB في مشترك كهربائي واحد موثوق.")
        self.assertNotContains(response, "FOR EVERY")
        self.assertNotContains(response, "Popular categories")
        self.assertNotContains(response, "6-Outlet USB Power Strip")
        self.assertContains(response, "English")
        self.assertContains(response, "hero-ev-original.webp")

        self.client.post(reverse("set_language"), {"language": "en", "next": reverse("core:home")})
        response = self.client.get(reverse("core:home"))
        self.assertContains(response, '<html lang="en" dir="ltr">', html=False)
        self.assertContains(response, "ELECTRICAL &amp; EV SOLUTIONS")
        self.assertContains(response, "hero-ev-original.webp")

    def test_first_visit_defaults_to_english_and_mobile_drawer_is_closed(self):
        response = self.client.get(reverse("core:home"), HTTP_ACCEPT_LANGUAGE="ar-EG,ar;q=0.9")
        self.assertContains(response, '<html lang="en" dir="ltr">', html=False)
        self.assertContains(response, '<div class="mobile-drawer" aria-hidden="true">', html=False)

    def test_homepage_has_no_artificial_render_delay_or_blocking_remote_fonts(self):
        response = self.client.get(reverse("core:home"))
        self.assertNotContains(response, "page-intro")
        self.assertNotContains(response, "fonts.googleapis.com")
        self.assertNotContains(response, '<script src="/static/js/vendor/lucide.min.js" defer>', html=False)
        self.assertContains(response, 'data-icon-library="/static/js/vendor/lucide-storefront.min.js"', html=False)
        self.assertContains(response, 'fetchpriority="high" media="(max-width: 700px)"', html=False)

    def test_health_and_legal_pages(self):
        self.assertEqual(self.client.get(reverse("core:health")).status_code, 200)
        self.assertEqual(self.client.get(reverse("core:health"))["X-Robots-Tag"], "noindex, nofollow, noarchive")
        for name in ("privacy", "terms", "shipping_policy", "returns_policy"):
            self.assertEqual(self.client.get(reverse(f"core:{name}")).status_code, 200)

    def test_sitemap_contains_indexable_category_pages(self):
        from catalog.models import Category, Product
        category = Category.objects.create(name="Power Strips", slug="test-power-strips")
        Product.objects.create(
            name="Test Strip", slug="test-strip", sku="STRIP-SEO", category=category,
            short_description="A safe power strip", description="Product description", price=250,
        )
        response = self.client.get(reverse("core:sitemap"))
        self.assertContains(response, f"http://testserver{category.get_absolute_url()}")
        self.assertContains(response, "http://testserver/products/test-strip/")

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

    def test_hero_link_keeps_a_descriptive_name_when_button_text_is_blank(self):
        Banner.objects.create(
            title="ROCKS",
            link=reverse("core:about"),
            button_text="   ",
            location="hero",
            is_active=True,
        )
        response = self.client.get(reverse("core:home"))
        self.assertContains(response, 'href="/about/"')
        self.assertContains(response, "Explore electrical products")

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
