from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient

from accounts.models import Favorite
from catalog.models import Category, Product


class FavoritesAPITests(TestCase):
    def test_favorites_are_private_and_idempotent(self):
        client = APIClient()
        category = Category.objects.create(name="Chargers", slug="chargers", is_active=True)
        product = Product.objects.create(
            category=category, name="Charger", slug="charger", sku="CHARGER-1",
            price="100.00", stock_quantity=2, is_active=True,
        )
        url = reverse("api:favorite-list")
        self.assertEqual(client.get(url).status_code, 401)

        user = get_user_model().objects.create_user(username="favoriteuser", password="SecurePass123!")
        client.force_authenticate(user=user)
        self.assertEqual(client.post(url, {"product_id": product.id}, format="json").status_code, 201)
        self.assertEqual(client.post(url, {"product_id": product.id}, format="json").status_code, 200)
        self.assertEqual(Favorite.objects.count(), 1)
        self.assertEqual(client.get(url).data["count"], 1)
        self.assertEqual(client.delete(reverse("api:favorite-detail", kwargs={"pk": product.id})).status_code, 204)
        self.assertEqual(Favorite.objects.count(), 0)
