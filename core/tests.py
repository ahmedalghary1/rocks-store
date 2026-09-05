from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase
from django.urls import reverse

from marketing.models import Subscriber
from .models import ContactMessage


class PublicPagesTests(TestCase):
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
