from django.conf import settings
from django.test import Client, TestCase
from django.urls import reverse
from unittest.mock import patch

from catalog.models import Category, Product


FACEBOOK_ANDROID = (
    "Mozilla/5.0 (Linux; Android 13; Pixel 7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36 "
    "[FB_IAB/FB4A;FBAV/450.0.0.0.0;]"
)


class InAppBrowserSessionTests(TestCase):
    def setUp(self):
        category = Category.objects.create(name="Tools", slug="browser-tools")
        self.product = Product.objects.create(
            name="Tester", slug="browser-tester", sku="BROWSER-1",
            category=category, price=120, stock_quantity=5,
            short_description="Tester", description="Test product",
        )
        self.browser = Client(enforce_csrf_checks=True, HTTP_USER_AGENT=FACEBOOK_ANDROID)
        self.headers = {
            "secure": True,
            "HTTP_ORIGIN": "https://testserver",
            "HTTP_X_REQUESTED_WITH": "XMLHttpRequest",
        }

    def bootstrap(self):
        response = self.browser.get(reverse("cart:session"), secure=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn("no-store", response["Cache-Control"])
        return response.json()["csrfToken"]

    def test_prefetched_page_without_cookies_can_recover_cart_and_wishlist(self):
        page = self.browser.get(
            self.product.get_absolute_url(), {"fbclid": "advert-test"}, secure=True,
            HTTP_REFERER="https://l.facebook.com/",
        )
        self.assertContains(page, 'data-csrf-token="')
        self.assertContains(page, 'data-session-url="/cart/session/"')
        stale_token = self.browser.cookies[settings.CSRF_COOKIE_NAME].value
        self.browser.cookies.clear()  # Prefetch HTML survived, its cookies did not.
        add_url = reverse("cart:add", args=[self.product.pk])
        failed = self.browser.post(
            add_url, {"quantity": 1, "csrfmiddlewaretoken": stale_token}, **self.headers,
        )
        self.assertEqual(failed.status_code, 403)
        self.assertEqual(failed.json()["code"], "csrf_failed")
        self.assertNotIn(settings.SESSION_COOKIE_NAME, self.browser.cookies)

        token = self.bootstrap()
        added = self.browser.post(
            add_url, {"quantity": 1, "csrfmiddlewaretoken": token}, **self.headers,
        )
        self.assertEqual(added.status_code, 200)
        self.assertEqual(added.json()["count"], 1)
        wished = self.browser.post(
            reverse("core:wishlist_toggle", args=[self.product.pk]),
            HTTP_X_CSRFTOKEN=token, **self.headers,
        )
        self.assertEqual(wished.status_code, 200)
        self.assertTrue(wished.json()["active"])
        self.assertEqual(self.browser.session["cart"], {str(self.product.pk): 1})
        self.assertEqual(self.browser.session["wishlist"], [self.product.pk])

    def test_stale_form_field_must_be_refreshed_even_with_valid_header(self):
        token = self.bootstrap()
        url = reverse("cart:add", args=[self.product.pk])
        failed = self.browser.post(
            url, {"quantity": 1, "csrfmiddlewaretoken": "a" * 64},
            HTTP_X_CSRFTOKEN=token, **self.headers,
        )
        self.assertEqual(failed.status_code, 403)
        self.assertFalse(self.browser.session.get("cart"))
        added = self.browser.post(
            url, {"quantity": 1, "csrfmiddlewaretoken": token},
            HTTP_X_CSRFTOKEN=token, **self.headers,
        )
        self.assertEqual(added.json()["count"], 1)

    def test_refresh_preserves_existing_session_and_cart(self):
        token = self.bootstrap()
        self.browser.post(
            reverse("cart:add", args=[self.product.pk]),
            {"quantity": 2, "csrfmiddlewaretoken": token}, **self.headers,
        )
        session_key = self.browser.session.session_key
        self.bootstrap()
        self.assertEqual(self.browser.session.session_key, session_key)
        self.assertEqual(self.browser.session["cart"], {str(self.product.pk): 2})

    def test_masked_token_works_with_httponly_csrf_cookie(self):
        with self.settings(CSRF_COOKIE_HTTPONLY=True):
            token = self.bootstrap()
            self.assertTrue(self.browser.cookies[settings.CSRF_COOKIE_NAME]["httponly"])
            response = self.browser.post(
                reverse("core:wishlist_toggle", args=[self.product.pk]),
                HTTP_X_CSRFTOKEN=token, **self.headers,
            )
            self.assertEqual(response.status_code, 200)

    def test_cross_origin_post_remains_rejected_after_refresh(self):
        token = self.bootstrap()
        headers = {**self.headers, "HTTP_ORIGIN": "https://facebook.com"}
        response = self.browser.post(
            reverse("cart:add", args=[self.product.pk]),
            {"quantity": 1, "csrfmiddlewaretoken": token}, **headers,
        )
        self.assertEqual(response.status_code, 403)
        self.assertFalse(self.browser.session.get("cart"))

    def test_standard_form_keeps_html_csrf_failure(self):
        response = self.browser.post(
            reverse("cart:add", args=[self.product.pk]), {"quantity": 1},
            secure=True, HTTP_ORIGIN="https://testserver",
        )
        self.assertEqual(response.status_code, 403)
        self.assertTrue(response["Content-Type"].startswith("text/html"))

    def test_same_origin_referer_works_without_origin_header(self):
        token = self.bootstrap()
        response = self.browser.post(
            reverse("cart:add", args=[self.product.pk]),
            {"quantity": 1, "csrfmiddlewaretoken": token}, secure=True,
            HTTP_REFERER=f"https://testserver{self.product.get_absolute_url()}",
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        self.assertEqual(response.status_code, 200)

    def test_arabic_translation_cannot_modify_security_tokens(self):
        self.browser.cookies[settings.LANGUAGE_COOKIE_NAME] = "ar"
        token = "Home" * 16
        with patch("cart.views.get_token", return_value=token):
            response = self.browser.get(reverse("cart:session"), secure=True)
        self.assertEqual(response.json()["csrfToken"], token)
