from unittest import mock

from django.core import mail

from Apps.Authentication_App.testing import BaseAPITestCase
from .models import Contact

VALID = {
    "first_name": "Visitor",
    "last_name": "One",
    "email": "visitor@example.com",
    "phone_number": "+911234567890",
    "subject": "Hello",
    "message": "I'd like to hire you.",
}


class ContactCreateTests(BaseAPITestCase):
    url = "/Contact/create/"

    def test_anonymous_can_submit(self):
        res = self.client.post(self.url, VALID, format="json")
        self.assertEqual(res.status_code, 201, res.content)
        self.assertTrue(res.json()["success"])
        self.assertEqual(Contact.objects.count(), 1)
        # Confirmation to visitor + notification to admin.
        self.assertEqual(len(mail.outbox), 2)

    def test_submission_with_expired_token_still_works(self):
        # The public form must not fail just because the visitor has a stale JWT.
        self.client.credentials(HTTP_AUTHORIZATION="Bearer expired.invalid.token")
        res = self.client.post(self.url, VALID, format="json")
        self.assertEqual(res.status_code, 201)

    def test_validation_errors(self):
        res = self.client.post(self.url, {**VALID, "email": "nope"}, format="json")
        self.assertEqual(res.status_code, 400)
        self.assertFalse(res.json()["success"])
        self.assertIn("email", res.json()["errors"])
        res = self.client.post(self.url, {}, format="json")
        self.assertEqual(res.status_code, 400)

    def test_email_failure_does_not_lose_submission(self):
        with mock.patch("Apps.Contact_App.views.send_mail", side_effect=OSError("smtp down")):
            res = self.client.post(self.url, VALID, format="json")
        self.assertEqual(res.status_code, 201)
        self.assertEqual(Contact.objects.count(), 1)


class ContactAdminTests(BaseAPITestCase):
    def setUp(self):
        super().setUp()
        self.contact = Contact.objects.create(**VALID)

    def test_anonymous_cannot_read_or_delete(self):
        self.assertEqual(self.client.get("/Contact/list/").status_code, 401)
        self.assertEqual(self.client.get(f"/Contact/list/{self.contact.id}/").status_code, 401)
        self.assertEqual(self.client.delete(f"/Contact/list/{self.contact.id}/").status_code, 401)
        self.assertTrue(Contact.objects.filter(id=self.contact.id).exists())

    def test_regular_user_cannot_read(self):
        self.auth(self.user)
        self.assertEqual(self.client.get("/Contact/list/").status_code, 403)

    def test_admin_can_list_read_delete(self):
        self.auth(self.admin)
        res = self.client.get("/Contact/list/")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(len(res.json()), 1)
        self.assertEqual(self.client.get(f"/Contact/list/{self.contact.id}/").status_code, 200)
        self.assertEqual(self.client.delete(f"/Contact/list/{self.contact.id}/").status_code, 204)
        self.assertFalse(Contact.objects.exists())
