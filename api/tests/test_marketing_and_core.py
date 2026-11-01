from django.core.cache import cache
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from core.models import ContactMessage, SiteSettings
from marketing.models import Banner, Subscriber


class MarketingAndCoreAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        cache.clear()
        self.banner = Banner.objects.create(
            title="Promo Banner",
            location="promo",
            is_active=True,
            sort_order=1,
        )
        self.site_settings = SiteSettings.objects.create(
            company_name="ROCKS ELECTRIC",
            phone="01012345678",
            whatsapp="01012345678",
            email="info@rocks-ev.com",
        )

    def test_banners_list_and_location_filtering(self):
        url = reverse("api:marketing-banners")
        res = self.client.get(url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)

        # Filter location match
        res_promo = self.client.get(url, {"location": "promo"})
        self.assertEqual(len(res_promo.data), 1)

        # Filter location no match
        res_hero = self.client.get(url, {"location": "hero"})
        self.assertEqual(len(res_hero.data), 0)

    def test_newsletter_subscription(self):
        url = reverse("api:newsletter-subscribe")
        res = self.client.post(url, {"email": "subscriber@example.com"}, format="json")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertTrue(Subscriber.objects.filter(email="subscriber@example.com").exists())

    def test_site_settings(self):
        url = reverse("api:site-settings")
        res = self.client.get(url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["company_name"], "ROCKS ELECTRIC")
        self.assertEqual(res.data["whatsapp"], "01012345678")

    def test_contact_message_submission_and_rate_limit(self):
        url = reverse("api:contact-message")
        payload = {
            "name": "Ahmed",
            "phone": "01123456789",
            "email": "ahmed@example.com",
            "subject": "Installation Inquiry",
            "message": "I would like to install a home charger in Sheikh Zayed.",
        }
        res = self.client.post(url, payload, format="json")
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertTrue(ContactMessage.objects.filter(subject="Installation Inquiry").exists())

        # Immediate second request should be rate-limited (HTTP 429)
        res_repeat = self.client.post(url, payload, format="json")
        self.assertEqual(res_repeat.status_code, status.HTTP_429_TOO_MANY_REQUESTS)

