"""Shared helpers for the backend test suites."""
from django.contrib.auth.models import User
from rest_framework.test import APIClient, APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

STRONG_PASSWORD = "Sup3r-Secret-Pass!"


class BaseAPITestCase(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.admin = User.objects.create_superuser("admin", "admin@example.com", STRONG_PASSWORD)
        self.user = User.objects.create_user(
            "alice", "alice@example.com", STRONG_PASSWORD, first_name="Alice", last_name="Smith"
        )
        self.other = User.objects.create_user("bob", "bob@example.com", STRONG_PASSWORD)

    def auth(self, user):
        token = RefreshToken.for_user(user).access_token
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

    def logout(self):
        self.client.credentials()
