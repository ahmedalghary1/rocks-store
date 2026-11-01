from django.test import TestCase
from django.urls import reverse


class APIDocumentationTests(TestCase):
    def test_swagger_assets_are_allowed_by_content_security_policy(self):
        response = self.client.get(reverse("swagger-ui"))
        self.assertEqual(response.status_code, 200)
        self.assertIn("https://cdn.jsdelivr.net", response["Content-Security-Policy"])
        self.assertIn("'unsafe-inline'", response["Content-Security-Policy"])
