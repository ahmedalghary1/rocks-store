import json
import re
from xml.etree import ElementTree as ET

from django.test import TestCase, override_settings
from django.utils import translation

from catalog.models import Category, Product, ProductVariant
from core.models import SiteSettings


@override_settings(SITE_URL="https://rocks-ev.com")
class SearchVisibilityTests(TestCase):
    def setUp(self):
        translation.activate("en")
        self.addCleanup(translation.activate, "en")
        self.category = Category.objects.create(name="Power Strips", name_ar="المشتركات الكهربائية", slug="power-strips")
        self.product = Product.objects.create(category=self.category, name="ROCKS Power Strip", name_ar="مشترك كهرباء روكس",
            slug="strip", sku="STRIP-1", short_description='A strip with "USB"', short_description_ar='مشترك بمخارج "USB"',
            description="Product details", description_ar="تفاصيل المنتج", price="100.00", stock_quantity=3)

    def schemas(self, response):
        return [json.loads(raw) for raw in re.findall(r'<script type="application/ld\+json"[^>]*>(.*?)</script>', response.content.decode(), re.S)]

    def test_languages_are_stable_and_reciprocal_without_cookies(self):
        for cookie in ("en", "ar"):
            self.client.cookies["rocks_language"] = cookie
            for path, code in (("/products/strip/", "en"), ("/ar/products/strip/", "ar")):
                response = self.client.get(path)
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response["Content-Language"], code)
                self.assertContains(response, f'<link rel="canonical" href="https://rocks-ev.com{path}">')
                self.assertContains(response, 'hreflang="en" href="https://rocks-ev.com/products/strip/"')
                self.assertContains(response, 'hreflang="ar-EG" href="https://rocks-ev.com/ar/products/strip/"')
                schema = next(item for item in self.schemas(response) if item.get("@type") == "Product")
                self.assertEqual(schema["name"], self.product.name_ar if code == "ar" else self.product.name)
                self.assertEqual(schema["offers"]["price"], "100.00")

    def test_variant_prices_and_stock_replace_base_offer(self):
        ProductVariant.objects.create(product=self.product, sku="STRIP-2M", label="2m", price="180.50", stock_quantity=2)
        ProductVariant.objects.create(product=self.product, sku="STRIP-5M", label="5m", price=None, stock_quantity=0)
        ProductVariant.objects.create(product=self.product, sku="HIDDEN", label="Hidden", price="9.00", stock_quantity=3, is_active=False)
        response = self.client.get("/ar/products/strip/")
        schema = next(item for item in self.schemas(response) if item.get("@type") == "Product")
        self.assertEqual([offer["price"] for offer in schema["offers"]], ["180.50", "100.00"])
        self.assertEqual(schema["offers"][1]["availability"], "https://schema.org/OutOfStock")

    def test_unpriced_product_has_no_invented_offer(self):
        self.product.price = None
        self.product.save()
        response = self.client.get("/products/strip/")
        schema = next(item for item in self.schemas(response) if item.get("@type") == "Product")
        self.assertNotIn("offers", schema)

    def test_json_ld_cannot_close_script(self):
        self.product.name_ar = '</script><script>alert("x")</script>'
        self.product.save()
        response = self.client.get("/ar/products/strip/")
        schema = next(item for item in self.schemas(response) if item.get("@type") == "Product")
        self.assertEqual(schema["name"], self.product.name_ar)
        self.assertNotContains(response, '<script>alert("x")</script>')

    def test_sitemap_contains_both_languages_and_excludes_hidden_products(self):
        Product.objects.create(category=self.category, name="Hidden", slug="hidden", sku="HIDDEN", is_active=False)
        response = self.client.get("/sitemap.xml")
        root = ET.fromstring(response.content)
        ns = {"s": "http://www.sitemaps.org/schemas/sitemap/0.9", "x": "http://www.w3.org/1999/xhtml"}
        urls = [item.text for item in root.findall("s:url/s:loc", ns)]
        self.assertIn("https://rocks-ev.com/ar/products/strip/", urls)
        self.assertIn("https://rocks-ev.com/products/strip/", urls)
        self.assertIn("https://rocks-ev.com/ar/buying-guide/", urls)
        self.assertFalse(any("hidden" in url for url in urls))
        for node in root.findall("s:url", ns):
            self.assertEqual(len(node.findall("x:link", ns)), 2)

    def test_faq_schema_matches_visible_answers_in_both_languages(self):
        for path in ("/", "/ar/", "/buying-guide/", "/ar/buying-guide/"):
            response = self.client.get(path)
            faq = next(item for item in self.schemas(response) if item.get("@type") == "FAQPage")
            for item in faq["mainEntity"]:
                self.assertContains(response, item["name"])
                self.assertContains(response, item["acceptedAnswer"]["text"])

    def test_language_switch_preserves_filters_and_uses_relative_url(self):
        response = self.client.get("/products/?q=USB&sort=price-low")
        self.assertContains(response, 'value="/ar/products/?q=USB&amp;sort=price-low"')
        response = self.client.post("/i18n/setlang/", {"language": "ar", "next": "/ar/products/?q=USB&sort=price-low"})
        self.assertEqual(response.url, "/ar/products/?q=USB&sort=price-low")

    def test_private_and_auxiliary_arabic_endpoints_are_noindex(self):
        for path in ("/ar/wishlist/", "/ar/health/", "/ar/products/strip/quick-view/", "/ar/products/search/suggestions/", "/ar/missing/"):
            response = self.client.get(path)
            self.assertIn("noindex", response["X-Robots-Tag"])
        self.assertContains(self.client.get("/robots.txt"), "Sitemap: https://rocks-ev.com/sitemap.xml")

    def test_arabic_search_finds_arabic_product_name(self):
        response = self.client.get("/ar/products/", {"q": "مشترك كهرباء"})
        self.assertContains(response, self.product.name_ar)
        self.assertContains(response, 'content="noindex,follow"')

    def test_only_real_business_contacts_are_published(self):
        response = self.client.get("/")
        self.assertNotContains(response, "+201234567890")
        self.assertNotContains(response, "mailto:info@rocks-ev.com")
        self.assertNotContains(response, 'aria-label="LinkedIn"')
        SiteSettings.objects.create(company_name="ROCKS ELWSAM", phone="+20255550100", email="support@example.com",
            address="Store address", address_ar="عنوان المتجر", facebook="https://www.facebook.com/example")
        response = self.client.get("/ar/")
        store = self.schemas(response)[0]["@graph"][0]
        self.assertEqual(store["telephone"], "+20255550100")
        self.assertEqual(store["address"]["streetAddress"], "عنوان المتجر")
        self.assertEqual(store["sameAs"], ["https://www.facebook.com/example"])
        self.assertContains(response, "mailto:support@example.com")
