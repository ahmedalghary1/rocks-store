from decimal import Decimal
from io import BytesIO
from tempfile import TemporaryDirectory

from django.contrib.auth.models import Permission, User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.test import override_settings
from django.urls import reverse
from PIL import Image

from catalog.models import Category, HomepageProduct, Product, ProductImage, ProductVariant, SpecificationTemplate, WarrantyTemplate
from controlpanel.forms import ProductControlForm, form_for
from controlpanel.registry import RESOURCES
from marketing.models import Banner
from orders.models import Order, OrderItem


class ProductContentTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_superuser("content-admin", "content@example.com", "password")
        self.client.force_login(self.admin)
        category = Category.objects.create(name="Content", slug="content")
        self.products = [Product.objects.create(
            name=f"Product {index}", name_ar=f"منتج {index}", slug=f"content-{index}", sku=f"CONTENT-{index}",
            category=category, short_description="Short", short_description_ar="مختصر",
            description="Details", description_ar="تفاصيل", stock_quantity=1,
            specifications_text="Individual specs", specifications_text_ar="مواصفات خاصة",
            warranty_text="Individual warranty", warranty_text_ar="ضمان خاص",
        ) for index in range(3)]

    def test_shared_text_assignment_edit_reassignment_and_removal(self):
        for resource, model, field in (
            ("specification-templates", SpecificationTemplate, "specification_template"),
            ("warranty-templates", WarrantyTemplate, "warranty_template"),
        ):
            with self.subTest(resource=resource):
                payload = {"name": "Shared", "text": "Shared text", "text_ar": "نص مشترك",
                           "products": [p.pk for p in self.products[:2]]}
                response = self.client.post(reverse("controlpanel:create", args=(resource,)), payload)
                self.assertRedirects(response, reverse("controlpanel:list", args=(resource,)))
                template = model.objects.get(name="Shared")
                self.assertEqual(template.products.count(), 2)
                form = form_for(RESOURCES[resource])(instance=template)
                self.assertEqual(set(form.initial["products"]), {p.pk for p in self.products[:2]})
                payload.update(text="Updated shared text", text_ar="نص مشترك محدث",
                               products=[p.pk for p in self.products[1:]])
                self.client.post(reverse("controlpanel:edit", args=(resource, template.pk)), payload)
                self.products[0].refresh_from_db()
                self.assertIsNone(getattr(self.products[0], field))
                self.assertEqual(set(template.products.values_list("pk", flat=True)), {p.pk for p in self.products[1:]})
                for product in self.products[1:]:
                    self.assertContains(self.client.get(product.get_absolute_url()), "Updated shared text")
                replacement = model.objects.create(name="Replacement", text="Replacement", text_ar="بديل")
                payload.update(name="Replacement", products=[self.products[1].pk])
                self.client.post(reverse("controlpanel:edit", args=(resource, replacement.pk)), payload)
                self.assertEqual(set(template.products.values_list("pk", flat=True)), {self.products[2].pk})
                replacement.delete()
                self.products[1].refresh_from_db()
                self.assertIsNone(getattr(self.products[1], field))
                self.assertEqual(self.products[1].specifications_text, "Individual specs")
                self.assertEqual(self.products[1].warranty_text, "Individual warranty")

    def test_public_content_switches_language_and_escapes_markup(self):
        product = self.products[0]
        for shared in (False, True):
            if shared:
                product.specification_template = SpecificationTemplate.objects.create(
                    name="Specs", text="Shared specs <script>alert(1)</script>", text_ar="مواصفات مشتركة")
                product.warranty_template = WarrantyTemplate.objects.create(
                    name="Warranty", text="Shared warranty", text_ar="ضمان مشترك")
                product.save()
            self.client.cookies["rocks_language"] = "en"
            response = self.client.get(f"/products/{product.slug}/")
            self.assertContains(response, "Shared specs" if shared else "Individual specs")
            self.assertContains(response, "Shared warranty" if shared else "Individual warranty")
            if shared:
                self.assertContains(response, "&lt;script&gt;alert(1)&lt;/script&gt;")
                self.assertNotContains(response, "Individual specs")
            self.client.cookies["rocks_language"] = "ar"
            response = self.client.get(f"/ar/products/{product.slug}/")
            self.assertContains(response, "مواصفات مشتركة" if shared else "مواصفات خاصة")
            self.assertContains(response, "ضمان مشترك" if shared else "ضمان خاص")

    def test_product_create_and_edit_save_bilingual_content(self):
        product = self.products[0]
        payload = {name: getattr(product, name) for name in (
            "name", "name_ar", "slug", "sku", "short_description", "short_description_ar",
            "description", "description_ar", "specifications_text", "specifications_text_ar",
            "warranty_text", "warranty_text_ar", "stock_quantity",
        )}
        payload.update(category=product.category_id, is_active="on",
                       **{"lengths-TOTAL_FORMS": "0", "lengths-INITIAL_FORMS": "0"})
        response = self.client.post(reverse("controlpanel:edit", args=("products", product.pk)), payload)
        self.assertRedirects(response, reverse("controlpanel:list", args=("products",)))
        product.refresh_from_db()
        self.assertEqual(product.warranty_text_ar, "ضمان خاص")
        payload.update(slug="new-content", sku="NEW-CONTENT")
        response = self.client.post(reverse("controlpanel:create", args=("products",)), payload)
        self.assertRedirects(response, reverse("controlpanel:list", args=("products",)))
        self.assertEqual(Product.objects.get(slug="new-content").specifications_text_ar, "مواصفات خاصة")
        payload["warranty_text_ar"] = ""
        form = ProductControlForm(payload, instance=product)
        self.assertFalse(form.is_valid())
        self.assertIn("warranty_text_ar", form.errors)
        payload.update(warranty_text="", warranty_text_ar="ضمان")
        form = ProductControlForm(payload, instance=product)
        self.assertFalse(form.is_valid())
        self.assertIn("warranty_text", form.errors)

    def test_coming_soon_product_can_be_created_without_price(self):
        response = self.client.post(reverse("controlpanel:create", args=("products",)), {
            "name": "New launch", "name_ar": "إطلاق جديد", "slug": "new-launch", "sku": "NEW-LAUNCH",
            "category": self.products[0].category_id,
            "short_description": "Made by ROCKS", "short_description_ar": "صنعته روكس",
            "description": "Coming soon", "description_ar": "قريبًا",
            "price": "", "old_price": "", "stock_quantity": "0",
            "is_new": "on", "is_coming_soon": "on", "is_active": "on",
            "lengths-TOTAL_FORMS": "0", "lengths-INITIAL_FORMS": "0",
        })
        self.assertRedirects(response, reverse("controlpanel:list", args=("products",)))
        product = Product.objects.get(slug="new-launch")
        self.assertIsNone(product.price)
        self.assertTrue(product.is_new)
        self.assertTrue(product.is_coming_soon)
        public = self.client.get(product.get_absolute_url())
        self.assertContains(public, "Fresh from ROCKS")
        self.assertNotContains(public, 'class="price price--hero"')
        self.assertNotContains(public, 'id="detail-cart-form"')

    def test_multiple_gallery_uploads_and_primary_selection_preserve_product_data(self):
        def upload(name, color):
            data = BytesIO()
            Image.new("RGB", (64, 64), color).save(data, format="PNG")
            return SimpleUploadedFile(name, data.getvalue(), content_type="image/png")

        product = self.products[0]
        original_name = product.name
        payload = {
            "name": product.name, "name_ar": product.name_ar, "slug": product.slug, "sku": product.sku,
            "category": product.category_id, "short_description": product.short_description,
            "short_description_ar": product.short_description_ar, "description": product.description,
            "description_ar": product.description_ar, "stock_quantity": product.stock_quantity,
            "specifications_text": product.specifications_text,
            "specifications_text_ar": product.specifications_text_ar,
            "warranty_text": product.warranty_text, "warranty_text_ar": product.warranty_text_ar,
            "is_active": "on", "lengths-TOTAL_FORMS": "0", "lengths-INITIAL_FORMS": "0",
        }
        with TemporaryDirectory() as media_root, override_settings(MEDIA_ROOT=media_root):
            product.main_image = upload("original.png", "green")
            product.save(update_fields=("main_image",))
            response = self.client.post(
                reverse("controlpanel:edit", args=("products", product.pk)),
                {**payload, "gallery_primary": "new:1", "gallery_images": [
                    upload("first.png", "red"), upload("second.png", "blue")
                ]},
            )
            self.assertRedirects(response, reverse("controlpanel:list", args=("products",)))
            product.refresh_from_db()
            self.assertEqual(product.images.count(), 3)
            self.assertTrue(product.main_image)
            first_primary_name = product.main_image.name
            self.assertEqual(product.name, original_name)
            self.assertEqual(product.specifications_text, "Individual specs")
            gallery_first = product.images.order_by("sort_order").first()
            response = self.client.post(
                reverse("controlpanel:edit", args=("products", product.pk)),
                {**payload, "gallery_primary": f"existing:{gallery_first.pk}"},
            )
            self.assertRedirects(response, reverse("controlpanel:list", args=("products",)))
            product.refresh_from_db()
            self.assertEqual(product.images.count(), 4)
            self.assertTrue(product.main_image.storage.exists(product.main_image.name))
            self.assertNotEqual(product.main_image.name, first_primary_name)
            self.assertEqual(product.name, original_name)

    def test_main_image_can_be_replaced_when_product_has_gallery_images(self):
        def upload(name, color):
            data = BytesIO()
            Image.new("RGB", (64, 64), color).save(data, format="PNG")
            return SimpleUploadedFile(name, data.getvalue(), content_type="image/png")

        product = self.products[0]
        payload = {
            "name": product.name, "name_ar": product.name_ar, "slug": product.slug, "sku": product.sku,
            "category": product.category_id, "short_description": product.short_description,
            "short_description_ar": product.short_description_ar, "description": product.description,
            "description_ar": product.description_ar, "stock_quantity": product.stock_quantity,
            "specifications_text": product.specifications_text,
            "specifications_text_ar": product.specifications_text_ar,
            "warranty_text": product.warranty_text, "warranty_text_ar": product.warranty_text_ar,
            "is_active": "on", "gallery_primary": "current",
            "lengths-TOTAL_FORMS": "0", "lengths-INITIAL_FORMS": "0",
        }
        with TemporaryDirectory() as media_root, override_settings(MEDIA_ROOT=media_root):
            product.main_image = upload("original.png", "green")
            product.save(update_fields=("main_image",))
            original_main_name = product.main_image.name
            ProductImage.objects.create(
                product=product, image=upload("gallery.png", "blue"),
                alt_text=product.name, alt_text_ar=product.name_ar,
            )

            response = self.client.post(
                reverse("controlpanel:edit", args=("products", product.pk)),
                {**payload, "main_image": upload("replacement.png", "red")},
            )

            self.assertRedirects(response, reverse("controlpanel:list", args=("products",)))
            product.refresh_from_db()
            self.assertNotEqual(product.main_image.name, original_main_name)
            self.assertTrue(product.main_image.storage.exists(product.main_image.name))
            self.assertEqual(product.images.count(), 2)
            self.assertTrue(any("original.webp" in image.image.name for image in product.images.all()))
            self.assertFalse(any("replacement.webp" in image.image.name for image in product.images.all()))

    def test_conflicting_main_image_selection_returns_form_error(self):
        def upload(name, color):
            data = BytesIO()
            Image.new("RGB", (64, 64), color).save(data, format="PNG")
            return SimpleUploadedFile(name, data.getvalue(), content_type="image/png")

        product = self.products[0]
        with TemporaryDirectory() as media_root, override_settings(MEDIA_ROOT=media_root):
            gallery_image = ProductImage.objects.create(
                product=product, image=upload("gallery.png", "blue"),
                alt_text=product.name, alt_text_ar=product.name_ar,
            )
            response = self.client.post(
                reverse("controlpanel:edit", args=("products", product.pk)),
                {
                    "name": product.name, "name_ar": product.name_ar, "slug": product.slug, "sku": product.sku,
                    "category": product.category_id, "short_description": product.short_description,
                    "short_description_ar": product.short_description_ar, "description": product.description,
                    "description_ar": product.description_ar, "stock_quantity": product.stock_quantity,
                    "specifications_text": product.specifications_text,
                    "specifications_text_ar": product.specifications_text_ar,
                    "warranty_text": product.warranty_text, "warranty_text_ar": product.warranty_text_ar,
                    "is_active": "on", "gallery_primary": f"existing:{gallery_image.pk}",
                    "lengths-TOTAL_FORMS": "0", "lengths-INITIAL_FORMS": "0",
                    "main_image": upload("replacement.png", "red"),
                },
            )

            self.assertEqual(response.status_code, 200)
            self.assertContains(response, "اختر طريقة واحدة لتحديد الصورة الرئيسية")
            product.refresh_from_db()
            self.assertFalse(product.main_image)

    def test_existing_product_images_can_be_deleted(self):
        def upload(name, color):
            data = BytesIO()
            Image.new("RGB", (64, 64), color).save(data, format="PNG")
            return SimpleUploadedFile(name, data.getvalue(), content_type="image/png")

        product = self.products[0]
        payload = {
            "name": product.name, "name_ar": product.name_ar, "slug": product.slug, "sku": product.sku,
            "category": product.category_id, "short_description": product.short_description,
            "short_description_ar": product.short_description_ar, "description": product.description,
            "description_ar": product.description_ar, "stock_quantity": product.stock_quantity,
            "specifications_text": product.specifications_text,
            "specifications_text_ar": product.specifications_text_ar,
            "warranty_text": product.warranty_text, "warranty_text_ar": product.warranty_text_ar,
            "is_active": "on", "lengths-TOTAL_FORMS": "0", "lengths-INITIAL_FORMS": "0",
        }
        with TemporaryDirectory() as media_root, override_settings(MEDIA_ROOT=media_root):
            product.main_image = upload("main.png", "green")
            product.save(update_fields=("main_image",))
            main_image_name = product.main_image.name
            gallery_image = ProductImage.objects.create(
                product=product, image=upload("gallery.png", "blue"),
                alt_text=product.name, alt_text_ar=product.name_ar,
            )
            gallery_image_name = gallery_image.image.name

            response = self.client.post(
                reverse("controlpanel:edit", args=("products", product.pk)),
                {
                    **payload,
                    "delete_main_image": "1",
                    "delete_gallery_images": [str(gallery_image.pk)],
                },
            )

            self.assertRedirects(response, reverse("controlpanel:list", args=("products",)))
            product.refresh_from_db()
            self.assertFalse(product.main_image)
            self.assertFalse(product.main_image.storage.exists(main_image_name))
            self.assertFalse(ProductImage.objects.filter(pk=gallery_image.pk).exists())
            self.assertFalse(product.images.model.image.field.storage.exists(gallery_image_name))

    def test_cannot_delete_gallery_image_selected_as_primary(self):
        def upload(name, color):
            data = BytesIO()
            Image.new("RGB", (64, 64), color).save(data, format="PNG")
            return SimpleUploadedFile(name, data.getvalue(), content_type="image/png")

        product = self.products[0]
        with TemporaryDirectory() as media_root, override_settings(MEDIA_ROOT=media_root):
            gallery_image = ProductImage.objects.create(
                product=product, image=upload("gallery.png", "blue"),
                alt_text=product.name, alt_text_ar=product.name_ar,
            )
            response = self.client.post(
                reverse("controlpanel:edit", args=("products", product.pk)),
                {
                    "name": product.name, "name_ar": product.name_ar, "slug": product.slug, "sku": product.sku,
                    "category": product.category_id, "short_description": product.short_description,
                    "short_description_ar": product.short_description_ar, "description": product.description,
                    "description_ar": product.description_ar, "stock_quantity": product.stock_quantity,
                    "specifications_text": product.specifications_text,
                    "specifications_text_ar": product.specifications_text_ar,
                    "warranty_text": product.warranty_text, "warranty_text_ar": product.warranty_text_ar,
                    "is_active": "on", "gallery_primary": f"existing:{gallery_image.pk}",
                    "delete_gallery_images": [str(gallery_image.pk)],
                    "lengths-TOTAL_FORMS": "0", "lengths-INITIAL_FORMS": "0",
                },
            )

            self.assertEqual(response.status_code, 200)
            self.assertContains(response, "لا يمكن تعيين صورة للحذف كصورة رئيسية")
            self.assertTrue(ProductImage.objects.filter(pk=gallery_image.pk).exists())

    def test_invalid_gallery_upload_does_not_change_product(self):
        product = self.products[0]
        response = self.client.post(reverse("controlpanel:edit", args=("products", product.pk)), {
            "name": "Changed name", "name_ar": product.name_ar, "slug": product.slug, "sku": product.sku,
            "category": product.category_id, "short_description": product.short_description,
            "short_description_ar": product.short_description_ar, "description": product.description,
            "description_ar": product.description_ar, "stock_quantity": product.stock_quantity,
            "specifications_text": product.specifications_text,
            "specifications_text_ar": product.specifications_text_ar,
            "warranty_text": product.warranty_text, "warranty_text_ar": product.warranty_text_ar,
            "is_active": "on", "gallery_primary": "new:0",
            "gallery_images": [SimpleUploadedFile("invalid.png", b"not an image", content_type="image/png")],
            "lengths-TOTAL_FORMS": "0", "lengths-INITIAL_FORMS": "0",
        })
        self.assertEqual(response.status_code, 200)
        product.refresh_from_db()
        self.assertEqual(product.name, "Product 0")
        self.assertFalse(product.images.exists())

    def test_invalid_shared_text_does_not_modify_products(self):
        response = self.client.post(reverse("controlpanel:create", args=("warranty-templates",)), {
            "name": "Incomplete", "text": "English only", "products": [self.products[0].pk],
        })
        self.assertEqual(response.status_code, 200)
        self.assertFalse(WarrantyTemplate.objects.exists())
        self.products[0].refresh_from_db()
        self.assertIsNone(self.products[0].warranty_template)

    def test_shared_assignment_requires_product_change_permission(self):
        staff = User.objects.create_user("content-staff", is_staff=True)
        staff.user_permissions.add(Permission.objects.get(codename="add_warrantytemplate"))
        self.client.force_login(staff)
        response = self.client.post(reverse("controlpanel:create", args=("warranty-templates",)), {
            "name": "Denied", "text": "Denied", "text_ar": "مرفوض", "products": [self.products[0].pk],
        })
        self.assertEqual(response.status_code, 403)
        self.assertFalse(WarrantyTemplate.objects.exists())


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
        self.assertContains(response, "lucide-storefront.min.js")
        self.assertNotContains(response, "lucide.min.js")
        self.assertNotContains(response, "fonts.googleapis.com")
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

    def test_product_editor_saves_lengths_with_independent_prices(self):
        category = Category.objects.create(name="Cables", slug="dashboard-length-cables")
        product = Product.objects.create(
            name="Charging Cable",
            name_ar="كابل شحن",
            slug="dashboard-length-cable",
            sku="CABLE-BASE",
            category=category,
            short_description="Charging cable with selectable lengths",
            short_description_ar="كابل شحن بأطوال متعددة",
            description="Cable details",
            description_ar="تفاصيل الكابل",
            price="100.00",
            stock_quantity=0,
        )
        self.client.force_login(self.admin)

        response = self.client.post(
            reverse("controlpanel:edit", args=("products", product.pk)),
            {
                "name": product.name,
                "name_ar": product.name_ar,
                "slug": product.slug,
                "sku": product.sku,
                "category": category.pk,
                "short_description": product.short_description,
                "short_description_ar": product.short_description_ar,
                "description": product.description,
                "description_ar": product.description_ar,
                "price": "100.00",
                "old_price": "",
                "stock_quantity": "0",
                "is_active": "on",
                "meta_title": "",
                "meta_title_ar": "",
                "meta_description": "",
                "meta_description_ar": "",
                "lengths-TOTAL_FORMS": "1",
                "lengths-INITIAL_FORMS": "0",
                "lengths-MIN_NUM_FORMS": "0",
                "lengths-MAX_NUM_FORMS": "1000",
                "lengths-0-label": "3 meters",
                "lengths-0-label_ar": "٣ متر",
                "lengths-0-sku": "CABLE-3M",
                "lengths-0-price": "275.00",
                "lengths-0-stock_quantity": "6",
                "lengths-0-is_active": "on",
            },
        )

        self.assertRedirects(response, reverse("controlpanel:list", args=("products",)))
        length = ProductVariant.objects.get(product=product)
        self.assertEqual(length.label, "3 meters")
        self.assertEqual(length.price, Decimal("275.00"))
        self.assertEqual(length.stock_quantity, 6)

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

    def test_orders_list_and_detail_keep_customer_and_products_together(self):
        category = Category.objects.create(name="Chargers", slug="chargers-order-test")
        product = Product.objects.create(
            name="Wall Charger", name_ar="شاحن جداري", slug="wall-charger-order-test",
            sku="WC-22", category=category, short_description="Fast charger",
            description="Order test product", price="12500.00", stock_quantity=3,
        )
        order = Order.objects.create(
            order_number="ROCKS-1001", customer_name="أحمد محمد", phone="01000000000",
            email="ahmed@example.com", governorate="القاهرة", city="مدينة نصر",
            address="شارع الاختبار، مبنى 10", notes="الاتصال قبل الوصول",
            subtotal="25000.00", shipping_cost="100.00", discount="0.00", total="25100.00",
        )
        OrderItem.objects.create(
            order=order, product=product, product_name=product.name, product_name_ar=product.name_ar,
            sku=product.sku, price="12500.00", quantity=2, total="25000.00",
        )
        self.client.force_login(self.admin)

        response = self.client.get(reverse("controlpanel:list", args=("orders",)))
        self.assertContains(response, "ROCKS-1001")
        self.assertContains(response, "أحمد محمد")
        self.assertContains(response, "شاحن جداري")
        self.assertNotContains(response, ">عناصر الطلبات<")

        response = self.client.get(reverse("controlpanel:edit", args=("orders", order.pk)))
        self.assertContains(response, "العميل وعنوان الاستلام")
        self.assertContains(response, "المنتجات المطلوبة")
        self.assertContains(response, "شاحن جداري")
        self.assertContains(response, "الاتصال قبل الوصول")

        response = self.client.post(reverse("controlpanel:edit", args=("orders", order.pk)), {
            "user": "", "coupon": "", "order_number": order.order_number, "customer_name": order.customer_name,
            "phone": order.phone, "email": order.email, "second_phone": "",
            "governorate": order.governorate, "city": order.city, "address": order.address,
            "notes": order.notes, "subtotal": order.subtotal, "shipping_cost": order.shipping_cost,
            "discount": order.discount, "total": order.total, "status": "confirmed",
            "payment_method": "cod", "payment_status": "unpaid", "save_continue": "1",
        })
        self.assertRedirects(response, reverse("controlpanel:edit", args=("orders", order.pk)))
        order.refresh_from_db()
        self.assertEqual(order.status, "confirmed")
