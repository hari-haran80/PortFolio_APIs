from datetime import timedelta
from unittest import mock

from django.contrib.auth.models import User
from django.core import mail
from django.test import override_settings
from django.utils import timezone
from rest_framework_simplejwt.tokens import RefreshToken

from .models import PasswordResetToken
from .testing import BaseAPITestCase, STRONG_PASSWORD


class HealthTests(BaseAPITestCase):
    def test_health(self):
        res = self.client.get("/Auth/health/")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json(), {"status": "ok"})


class RegisterTests(BaseAPITestCase):
    url = "/Auth/register/"

    def payload(self, **overrides):
        data = {
            "username": "newuser",
            "first_name": "New",
            "last_name": "User",
            "email": "new@example.com",
            "password": STRONG_PASSWORD,
        }
        data.update(overrides)
        return data

    def test_register_creates_user_profile_and_notifies_admin(self):
        res = self.client.post(self.url, self.payload(), format="json")
        self.assertEqual(res.status_code, 201, res.content)
        user = User.objects.get(username="newuser")
        self.assertTrue(user.check_password(STRONG_PASSWORD))
        self.assertTrue(hasattr(user, "profile"))
        self.assertEqual(len(mail.outbox), 1)
        self.assertNotIn("password", res.json())

    def test_register_rejects_weak_password(self):
        res = self.client.post(self.url, self.payload(password="123"), format="json")
        self.assertEqual(res.status_code, 400)
        self.assertIn("password", res.json())
        self.assertFalse(User.objects.filter(username="newuser").exists())

    def test_register_rejects_duplicate_username(self):
        res = self.client.post(self.url, self.payload(username="alice"), format="json")
        self.assertEqual(res.status_code, 400)
        self.assertIn("username", res.json())

    def test_register_rejects_duplicate_email_case_insensitive(self):
        res = self.client.post(self.url, self.payload(email="ALICE@example.com"), format="json")
        self.assertEqual(res.status_code, 400)
        self.assertIn("email", res.json())

    def test_register_requires_email_and_password(self):
        res = self.client.post(self.url, {"username": "x"}, format="json")
        self.assertEqual(res.status_code, 400)
        self.assertIn("email", res.json())
        self.assertIn("password", res.json())

    def test_register_cannot_create_superuser(self):
        res = self.client.post(self.url, self.payload(is_superuser=True, is_staff=True), format="json")
        self.assertEqual(res.status_code, 201)
        user = User.objects.get(username="newuser")
        self.assertFalse(user.is_superuser)
        self.assertFalse(user.is_staff)

    def test_register_succeeds_even_if_email_fails(self):
        with mock.patch("Apps.Authentication_App.views.send_mail", side_effect=OSError("smtp down")):
            res = self.client.post(self.url, self.payload(), format="json")
        self.assertEqual(res.status_code, 201)
        self.assertTrue(User.objects.filter(username="newuser").exists())


class LoginLogoutTests(BaseAPITestCase):
    def test_login_success_returns_tokens(self):
        res = self.client.post("/Auth/login/", {"username": "alice", "password": STRONG_PASSWORD}, format="json")
        self.assertEqual(res.status_code, 200)
        body = res.json()
        for key in ("access", "refresh", "user_id", "is_superuser", "theme", "last_login"):
            self.assertIn(key, body)
        self.assertEqual(body["user_id"], self.user.id)
        self.assertFalse(body["is_superuser"])

    def test_login_admin_flag(self):
        res = self.client.post("/Auth/login/", {"username": "admin", "password": STRONG_PASSWORD}, format="json")
        self.assertTrue(res.json()["is_superuser"])

    def test_login_wrong_password(self):
        res = self.client.post("/Auth/login/", {"username": "alice", "password": "nope"}, format="json")
        self.assertEqual(res.status_code, 401)
        self.assertEqual(res.json()["message"], "Invalid credentials")

    def test_login_missing_fields(self):
        res = self.client.post("/Auth/login/", {}, format="json")
        self.assertEqual(res.status_code, 400)

    def test_logout_blacklists_refresh_token(self):
        refresh = RefreshToken.for_user(self.user)
        self.auth(self.user)
        res = self.client.post("/Auth/logout/", {"refresh": str(refresh)}, format="json")
        self.assertEqual(res.status_code, 205)
        # The blacklisted refresh token can no longer be used.
        self.logout()
        res = self.client.post("/Auth/token/refresh/", {"refresh": str(refresh)}, format="json")
        self.assertEqual(res.status_code, 401)

    def test_logout_requires_auth_and_token(self):
        self.assertEqual(self.client.post("/Auth/logout/", {}, format="json").status_code, 401)
        self.auth(self.user)
        self.assertEqual(self.client.post("/Auth/logout/", {}, format="json").status_code, 400)
        self.assertEqual(self.client.post("/Auth/logout/", {"refresh": "garbage"}, format="json").status_code, 400)

    def test_token_refresh_and_verify(self):
        refresh = RefreshToken.for_user(self.user)
        res = self.client.post("/Auth/token/refresh/", {"refresh": str(refresh)}, format="json")
        self.assertEqual(res.status_code, 200)
        self.assertIn("access", res.json())
        self.assertEqual(self.client.get("/Auth/verify/").status_code, 401)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {res.json()['access']}")
        self.assertEqual(self.client.get("/Auth/verify/").status_code, 200)


class ChangePasswordTests(BaseAPITestCase):
    url = "/Auth/change-password/"

    def test_requires_auth(self):
        self.assertEqual(self.client.post(self.url, {}, format="json").status_code, 401)

    def test_wrong_old_password(self):
        self.auth(self.user)
        res = self.client.post(self.url, {"old_password": "bad", "new_password": "An0ther-Strong-Pass"}, format="json")
        self.assertEqual(res.status_code, 400)
        self.assertIn("message", res.json())

    def test_weak_new_password_rejected(self):
        self.auth(self.user)
        res = self.client.post(self.url, {"old_password": STRONG_PASSWORD, "new_password": "123"}, format="json")
        self.assertEqual(res.status_code, 400)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password(STRONG_PASSWORD))

    def test_success(self):
        self.auth(self.user)
        res = self.client.post(
            self.url, {"old_password": STRONG_PASSWORD, "new_password": "An0ther-Strong-Pass"}, format="json"
        )
        self.assertEqual(res.status_code, 200)
        self.assertIn("success", res.json()["message"].lower())
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password("An0ther-Strong-Pass"))


class DeleteUserTests(BaseAPITestCase):
    def test_user_cannot_delete_someone_else(self):
        self.auth(self.user)
        res = self.client.delete(f"/Auth/delete-user/{self.other.id}/")
        self.assertEqual(res.status_code, 403)
        self.assertTrue(User.objects.filter(id=self.other.id).exists())

    def test_user_can_delete_self(self):
        self.auth(self.user)
        self.assertEqual(self.client.delete(f"/Auth/delete-user/{self.user.id}/").status_code, 204)
        self.assertFalse(User.objects.filter(id=self.user.id).exists())

    def test_admin_can_delete_anyone_and_404(self):
        self.auth(self.admin)
        self.assertEqual(self.client.delete(f"/Auth/delete-user/{self.other.id}/").status_code, 204)
        self.assertEqual(self.client.delete("/Auth/delete-user/99999/").status_code, 404)


@override_settings(FRONTEND_URL="https://portfolio.example.com", PASSWORD_RESET_TOKEN_TTL_MINUTES=60)
class PasswordResetTests(BaseAPITestCase):
    def request_reset(self, email="alice@example.com"):
        return self.client.post("/Auth/forgot-password/", {"email": email}, format="json")

    def test_token_is_never_returned_in_response(self):
        res = self.request_reset()
        self.assertEqual(res.status_code, 200)
        token = PasswordResetToken.objects.get(user=self.user).token
        self.assertNotIn(token, res.content.decode())

    def test_email_contains_hash_router_link(self):
        self.request_reset()
        token = PasswordResetToken.objects.get(user=self.user).token
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn(f"https://portfolio.example.com/#/reset-password/{token}", mail.outbox[0].body)

    def test_unknown_email_gives_same_response(self):
        known = self.request_reset()
        unknown = self.request_reset("nobody@example.com")
        self.assertEqual(unknown.status_code, 200)
        self.assertEqual(known.json(), unknown.json())
        self.assertEqual(len(mail.outbox), 1)

    def test_new_request_invalidates_old_token(self):
        self.request_reset()
        first = PasswordResetToken.objects.get(user=self.user).token
        self.request_reset()
        self.assertFalse(PasswordResetToken.objects.filter(token=first).exists())
        self.assertEqual(PasswordResetToken.objects.filter(user=self.user).count(), 1)

    def test_full_reset_flow(self):
        self.request_reset()
        token = PasswordResetToken.objects.get(user=self.user).token
        res = self.client.post(
            f"/Auth/reset-password/{token}/",
            {"new_password": "Brand-New-Pass-42", "confirm_password": "Brand-New-Pass-42"},
            format="json",
        )
        self.assertEqual(res.status_code, 200)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password("Brand-New-Pass-42"))
        # Token is single use.
        res = self.client.post(
            f"/Auth/reset-password/{token}/",
            {"new_password": "Brand-New-Pass-43", "confirm_password": "Brand-New-Pass-43"},
            format="json",
        )
        self.assertEqual(res.status_code, 400)

    def test_mismatch_and_weak_password(self):
        self.request_reset()
        token = PasswordResetToken.objects.get(user=self.user).token
        res = self.client.post(
            f"/Auth/reset-password/{token}/", {"new_password": "a", "confirm_password": "b"}, format="json"
        )
        self.assertEqual(res.status_code, 400)
        res = self.client.post(
            f"/Auth/reset-password/{token}/", {"new_password": "123", "confirm_password": "123"}, format="json"
        )
        self.assertEqual(res.status_code, 400)
        self.assertTrue(PasswordResetToken.objects.filter(token=token).exists())

    def test_expired_token_rejected(self):
        self.request_reset()
        prt = PasswordResetToken.objects.get(user=self.user)
        PasswordResetToken.objects.filter(pk=prt.pk).update(created_at=timezone.now() - timedelta(hours=2))
        res = self.client.post(
            f"/Auth/reset-password/{prt.token}/",
            {"new_password": "Brand-New-Pass-42", "confirm_password": "Brand-New-Pass-42"},
            format="json",
        )
        self.assertEqual(res.status_code, 400)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password(STRONG_PASSWORD))

    def test_invalid_token(self):
        res = self.client.post(
            "/Auth/reset-password/not-a-token/",
            {"new_password": "Brand-New-Pass-42", "confirm_password": "Brand-New-Pass-42"},
            format="json",
        )
        self.assertEqual(res.status_code, 400)

    def test_invalid_email_format(self):
        self.assertEqual(self.request_reset("not-an-email").status_code, 400)
