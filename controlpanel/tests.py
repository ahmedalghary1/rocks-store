from django.contrib.auth.models import Permission, User
from django.test import TestCase
from django.urls import reverse

from catalog.models import Category, HomepageProduct, Product
from controlpanel.registry import RESOURCES
from marketing.models import Banner


class ControlPanelTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_superuser("panel-admin", "admin@example.com", "Strong-password-982!")

    def test_dashboard_requires_staff_login(self):
        response = self.client.get(reverse("controlpanel:index"))
        self.assertEqual(response.status_code, 302)
        self.assertIn("/dashboard/login/", response.url)

    def test_dashboard_has_separate_staff_login(self):
        response = self.client.get(reverse("controlpanel:login"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "دخول لوحة التحكم")
        response = self.client.post(reverse("controlpanel:login"), {"username": self.admin.username, "password": "Strong-password-982!"})
        self.assertRedirects(response, reverse("controlpanel:index"))

        customer = User.objects.create_user("customer", password="Customer-password-982!")
        self.client.logout()
        response = self.client.post(reverse("controlpanel:login"), {"username": customer.username, "password": "Customer-password-982!"})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "لا يملك صلاحية")

    def test_superuser_can_open_dashboard_and_resource_pages(self):
        self.client.force_login(self.admin)
        response = self.client.get(reverse("controlpanel:index"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "مركز الإدارة")
        self.assertContains(response, "controlpanel.css")
        self.assertContains(response, "controlpanel.js")
        response = self.client.get(reverse("controlpanel:list", args=("products",)))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "إدارة البيانات")

    def test_superuser_can_create_and_edit_category(self):
        self.client.force_login(self.admin)
        response = self.client.post(reverse("controlpanel:create", args=("categories",)), {
            "name": "Chargers", "name_ar": "الشواحن", "slug": "chargers", "description": "",
            "description_ar": "", "icon": "zap", "parent": "", "is_active": "on", "sort_order": "1",
        })
        self.assertRedirects(response, reverse("controlpanel:list", args=("categories",)))
        category = Category.objects.get(slug="chargers")
        response = self.client.post(reverse("controlpanel:edit", args=("categories", category.pk)), {
            "name": "EV Chargers", "name_ar": "شواحن السيارات", "slug": "chargers", "description": "",
            "description_ar": "", "icon": "zap", "parent": "", "is_active": "on", "sort_order": "2",
        })
        self.assertRedirects(response, reverse("controlpanel:list", args=("categories",)))
        category.refresh_from_db()
        self.assertEqual(category.name, "EV Chargers")

    def test_staff_permissions_are_enforced(self):
        staff = User.objects.create_user("catalog-staff", password="Strong-password-981!", is_staff=True)
        staff.user_permissions.add(Permission.objects.get(codename="view_product"))
        self.client.force_login(staff)
        self.assertEqual(self.client.get(reverse("controlpanel:list", args=("products",))).status_code, 200)
        self.assertEqual(self.client.get(reverse("controlpanel:create", args=("products",))).status_code, 403)
        self.assertEqual(self.client.get(reverse("controlpanel:list", args=("orders",))).status_code, 403)

    def test_csv_export_uses_utf8(self):
        self.client.force_login(self.admin)
        response = self.client.get(reverse("controlpanel:list", args=("categories",)), {"export": "csv"})
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.content.startswith(b"\xef\xbb\xbf"))

    def test_hero_banner_content_is_connected_to_storefront(self):
        Banner.objects.create(
            title="FAST CHARGING FUTURE",
            title_ar="مستقبل الشحن السريع",
            subtitle="Managed from the control panel",
            subtitle_ar="يُدار من لوحة التحكم",
            button_text="Discover",
            button_text_ar="اكتشف",
            location="hero",
            is_active=True,
        )
        response = self.client.get(reverse("core:home"))
        self.assertContains(response, "FAST CHARGING FUTURE")
        self.assertContains(response, "Managed from the control panel")

    def test_every_registered_management_section_renders(self):
        self.client.force_login(self.admin)
        for resource in RESOURCES:
            with self.subTest(resource=resource):
                self.assertEqual(self.client.get(reverse("controlpanel:list", args=(resource,))).status_code, 200)
                self.assertEqual(self.client.get(reverse("controlpanel:create", args=(resource,))).status_code, 200)

    def test_selected_homepage_products_control_storefront(self):
        category = Category.objects.create(name="Home products", slug="home-products")
        selected = Product.objects.create(
            name="Selected homepage product", slug="selected-home-product", sku="HOME-1", category=category,
            short_description="Selected from the dashboard", description="Details", price="100.00", stock_quantity=4,
        )
        Product.objects.create(
            name="Unselected featured product", slug="unselected-featured", sku="HOME-2", category=category,
            short_description="Should not be shown", description="Details", price="120.00", stock_quantity=4, is_featured=True,
        )
        self.client.force_login(self.admin)
        response = self.client.post(reverse("controlpanel:create", args=("homepage-products",)), {
            "product": selected.pk, "sort_order": 1, "is_active": "on",
        })
        self.assertRedirects(response, reverse("controlpanel:list", args=("homepage-products",)))
        self.assertTrue(HomepageProduct.objects.filter(product=selected).exists())
        response = self.client.get(reverse("core:home"))
        self.assertContains(response, "Selected homepage product")
        self.assertNotContains(response, "Unselected featured product")
