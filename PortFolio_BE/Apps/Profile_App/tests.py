from django.contrib.auth.models import User

from Apps.Authentication_App.testing import BaseAPITestCase
from .models import Profile


class ProfileSignalTests(BaseAPITestCase):
    def test_profile_created_for_every_user(self):
        u = User.objects.create_user("carol", "carol@example.com", "x")
        self.assertTrue(Profile.objects.filter(user=u).exists())
        self.assertEqual(Profile.objects.filter(user=u).count(), 1)


class ProfileListTests(BaseAPITestCase):
    url = "/User/profiles/"

    def test_anonymous_cannot_list_profiles(self):
        self.assertEqual(self.client.get(self.url).status_code, 401)

    def test_regular_user_cannot_list_profiles(self):
        self.auth(self.user)
        self.assertEqual(self.client.get(self.url).status_code, 403)

    def test_admin_can_list_profiles(self):
        self.auth(self.admin)
        res = self.client.get(self.url)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(len(res.json()), 3)
        first = res.json()[0]
        self.assertIn("profile_picture", first)
        self.assertNotIn("password", first["user"])


class ProfileDetailTests(BaseAPITestCase):
    def url(self, user):
        return f"/User/profiles/{user.id}/"

    def test_lookup_is_by_user_id(self):
        # Make profile ids and user ids diverge, which is what happens in a real DB.
        Profile.objects.filter(user=self.user).delete()
        Profile.objects.create(user=self.user)
        self.assertNotEqual(self.user.profile.id, self.user.id)
        self.auth(self.user)
        res = self.client.get(self.url(self.user))
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["user"]["id"], self.user.id)

    def test_anonymous_cannot_read(self):
        self.assertEqual(self.client.get(self.url(self.user)).status_code, 401)

    def test_user_can_read_and_update_own_profile(self):
        self.auth(self.user)
        res = self.client.patch(
            self.url(self.user),
            {"user.first_name": "Alicia", "user.email": "alicia@example.com", "position": "Engineer"},
            format="multipart",
        )
        self.assertEqual(res.status_code, 200, res.content)
        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, "Alicia")
        self.assertEqual(self.user.email, "alicia@example.com")
        self.assertEqual(self.user.profile.position, "Engineer")

    def test_user_can_resubmit_own_username(self):
        self.auth(self.user)
        res = self.client.patch(self.url(self.user), {"user.username": "alice"}, format="multipart")
        self.assertEqual(res.status_code, 200, res.content)

    def test_user_cannot_take_someone_elses_username_or_email(self):
        self.auth(self.user)
        res = self.client.patch(self.url(self.user), {"user.username": "bob"}, format="multipart")
        self.assertEqual(res.status_code, 400)
        res = self.client.patch(self.url(self.user), {"user.email": "bob@example.com"}, format="multipart")
        self.assertEqual(res.status_code, 400)

    def test_user_cannot_read_or_edit_other_profile(self):
        self.auth(self.user)
        self.assertEqual(self.client.get(self.url(self.other)).status_code, 403)
        res = self.client.patch(self.url(self.other), {"position": "Hacked"}, format="multipart")
        self.assertEqual(res.status_code, 403)
        self.assertEqual(self.client.delete(self.url(self.other)).status_code, 403)

    def test_user_cannot_make_self_superuser(self):
        self.auth(self.user)
        res = self.client.patch(self.url(self.user), {"user.is_superuser": "true"}, format="multipart")
        self.assertEqual(res.status_code, 200)
        self.user.refresh_from_db()
        self.assertFalse(self.user.is_superuser)
        self.assertFalse(self.user.is_staff)

    def test_admin_can_promote_user(self):
        self.auth(self.admin)
        res = self.client.patch(self.url(self.user), {"user.is_superuser": "true"}, format="multipart")
        self.assertEqual(res.status_code, 200)
        self.user.refresh_from_db()
        self.assertTrue(self.user.is_superuser)
        self.assertTrue(self.user.is_staff)

    def test_user_can_delete_own_profile(self):
        self.auth(self.user)
        self.assertEqual(self.client.delete(self.url(self.user)).status_code, 204)
        self.assertFalse(User.objects.filter(id=self.user.id).exists())

    def test_admin_can_delete_other_profile(self):
        self.auth(self.admin)
        self.assertEqual(self.client.delete(self.url(self.other)).status_code, 204)
        self.assertFalse(User.objects.filter(id=self.other.id).exists())

    def test_missing_profile_404(self):
        self.auth(self.admin)
        self.assertEqual(self.client.get("/User/profiles/99999/").status_code, 404)
