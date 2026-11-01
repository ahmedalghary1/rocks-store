from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from accounts.models import Address

User = get_user_model()


class AuthAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user_password = "SecurePassword123!"
        self.user = User.objects.create_user(
            username="existinguser",
            email="existing@example.com",
            password=self.user_password,
            first_name="Existing",
            last_name="User",
        )

    def test_registration_success(self):
        url = reverse("api:auth-register")
        payload = {
            "username": "newuser",
            "email": "newuser@example.com",
            "password": "StrongPassword123!",
            "password_confirm": "StrongPassword123!",
            "first_name": "New",
            "last_name": "Customer",
        }
        response = self.client.post(url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn("tokens", response.data)
        self.assertIn("access", response.data["tokens"])
        self.assertIn("refresh", response.data["tokens"])
        self.assertEqual(response.data["username"], "newuser")
        self.assertTrue(User.objects.filter(username="newuser").exists())

    def test_registration_mismatched_password(self):
        url = reverse("api:auth-register")
        payload = {
            "username": "mismatch",
            "email": "mismatch@example.com",
            "password": "StrongPassword123!",
            "password_confirm": "DifferentPassword123!",
        }
        response = self.client.post(url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("password_confirm", response.data)

    def test_registration_duplicate_email(self):
        url = reverse("api:auth-register")
        payload = {
            "username": "anotheruser",
            "email": "existing@example.com",
            "password": "StrongPassword123!",
            "password_confirm": "StrongPassword123!",
        }
        response = self.client.post(url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("email", response.data)

    def test_login_jwt_token(self):
        url = reverse("api:token_obtain_pair")
        payload = {"username": "existinguser", "password": self.user_password}
        response = self.client.post(url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)

    def test_token_refresh(self):
        url = reverse("api:token_obtain_pair")
        res = self.client.post(url, {"username": "existinguser", "password": self.user_password}, format="json")
        refresh = res.data["refresh"]

        refresh_url = reverse("api:token_refresh")
        refresh_res = self.client.post(refresh_url, {"refresh": refresh}, format="json")
        self.assertEqual(refresh_res.status_code, status.HTTP_200_OK)
        self.assertIn("access", refresh_res.data)

        logout_res = self.client.post(reverse("api:token_blacklist"), {"refresh": refresh_res.data["refresh"]}, format="json")
        self.assertEqual(logout_res.status_code, status.HTTP_200_OK)
        rejected = self.client.post(refresh_url, {"refresh": refresh_res.data["refresh"]}, format="json")
        self.assertEqual(rejected.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_user_profile(self):
        self.client.force_authenticate(user=self.user)
        url = reverse("api:auth-me")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["email"], "existing@example.com")

        # Update profile
        update_res = self.client.patch(url, {"first_name": "UpdatedName"}, format="json")
        self.assertEqual(update_res.status_code, status.HTTP_200_OK)
        self.assertEqual(update_res.data["first_name"], "UpdatedName")

    def test_change_password(self):
        self.client.force_authenticate(user=self.user)
        url = reverse("api:auth-change-password")
        payload = {
            "old_password": self.user_password,
            "new_password": "NewStrongPass987!",
            "confirm_password": "NewStrongPass987!",
        }
        response = self.client.post(url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Verify old password no longer works
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password("NewStrongPass987!"))

    def test_addresses_crud_and_set_default(self):
        self.client.force_authenticate(user=self.user)
        list_url = reverse("api:address-list")

        # Create address
        payload = {
            "label": "Work",
            "recipient_name": "Mohamed",
            "phone": "01012345678",
            "governorate": "Cairo",
            "city": "Nasr City",
            "address_line": "15 Abbas El Akkad",
            "is_default": True,
        }
        res = self.client.post(list_url, payload, format="json")
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        addr_id = res.data["id"]

        # Create second address
        payload2 = {
            "label": "Home",
            "recipient_name": "Mohamed Home",
            "phone": "01012345678",
            "governorate": "Giza",
            "city": "Dokki",
            "address_line": "10 Tahrir St",
            "is_default": False,
        }
        res2 = self.client.post(list_url, payload2, format="json")
        self.assertEqual(res2.status_code, status.HTTP_201_CREATED)
        addr2_id = res2.data["id"]

        # Set second address as default
        set_def_url = reverse("api:address-set-default", kwargs={"pk": addr2_id})
        set_def_res = self.client.post(set_def_url)
        self.assertEqual(set_def_res.status_code, status.HTTP_200_OK)
        self.assertTrue(set_def_res.data["is_default"])

        # Check that first address is no longer default
        addr1 = Address.objects.get(pk=addr_id)
        self.assertFalse(addr1.is_default)

