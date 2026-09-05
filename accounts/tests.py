from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse


class AccountTests(TestCase):
    def test_registration_normalizes_and_rejects_duplicate_email(self):
        payload = {"username": "first", "email": "USER@Example.com", "password1": "A-long-password-987!", "password2": "A-long-password-987!"}
        response = self.client.post(reverse("accounts:register"), payload)
        self.assertRedirects(response, reverse("accounts:dashboard"))
        self.assertEqual(get_user_model().objects.get().email, "user@example.com")
        self.client.logout()
        payload["username"] = "second"
        response = self.client.post(reverse("accounts:register"), payload)
        self.assertContains(response, "An account with this email already exists")

    def test_dashboard_requires_login(self):
        response = self.client.get(reverse("accounts:dashboard"))
        self.assertRedirects(response, f"{reverse('login')}?next={reverse('accounts:dashboard')}")
