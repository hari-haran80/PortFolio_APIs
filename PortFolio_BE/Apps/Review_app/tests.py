from unittest import mock

from django.core import mail

from Apps.Authentication_App.testing import BaseAPITestCase
from .models import Review


class ReviewTests(BaseAPITestCase):
    url = "/User/reviews/"

    def test_anyone_can_list_reviews_with_user_info(self):
        Review.objects.create(user=self.user, rating=5, comment="Great")
        res = self.client.get(self.url)
        self.assertEqual(res.status_code, 200)
        item = res.json()[0]
        self.assertEqual(item["user"]["username"], "alice")
        self.assertIn("profile_picture", item["user"])
        self.assertNotIn("email", item["user"])

    def test_anonymous_cannot_create(self):
        self.assertEqual(self.client.post(self.url, {"rating": 5, "comment": "x"}, format="json").status_code, 401)

    def test_create_review_sets_owner_and_notifies(self):
        self.auth(self.user)
        res = self.client.post(self.url, {"rating": 4, "comment": "Nice work", "user": self.other.id}, format="json")
        self.assertEqual(res.status_code, 201, res.content)
        review = Review.objects.get()
        self.assertEqual(review.user, self.user)  # cannot spoof the author
        self.assertEqual(len(mail.outbox), 1)

    def test_rating_must_be_1_to_5(self):
        self.auth(self.user)
        for bad in (0, 6, -1):
            res = self.client.post(self.url, {"rating": bad, "comment": "x"}, format="json")
            self.assertEqual(res.status_code, 400, bad)

    def test_comment_required(self):
        self.auth(self.user)
        self.assertEqual(self.client.post(self.url, {"rating": 5, "comment": ""}, format="json").status_code, 400)

    def test_one_review_per_user(self):
        self.auth(self.user)
        self.client.post(self.url, {"rating": 5, "comment": "First"}, format="json")
        res = self.client.post(self.url, {"rating": 4, "comment": "Second"}, format="json")
        self.assertEqual(res.status_code, 400)
        self.assertEqual(Review.objects.count(), 1)

    def test_email_failure_still_saves_review(self):
        self.auth(self.user)
        with mock.patch("Apps.Review_app.views.send_mail", side_effect=OSError("smtp down")):
            res = self.client.post(self.url, {"rating": 5, "comment": "Great"}, format="json")
        self.assertEqual(res.status_code, 201)

    def test_only_owner_or_admin_can_edit_or_delete(self):
        review = Review.objects.create(user=self.user, rating=5, comment="Great")
        detail = f"{self.url}{review.id}/"

        self.auth(self.other)
        self.assertEqual(self.client.patch(detail, {"comment": "hacked"}, format="json").status_code, 403)
        self.assertEqual(self.client.delete(detail).status_code, 403)

        self.auth(self.user)
        res = self.client.patch(detail, {"comment": "Updated"}, format="json")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["comment"], "Updated")

        self.auth(self.admin)
        self.assertEqual(self.client.delete(detail).status_code, 204)
        self.assertFalse(Review.objects.exists())
