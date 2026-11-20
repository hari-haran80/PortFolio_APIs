import base64
from unittest import mock

from django.core.mail import EmailMultiAlternatives, get_connection, send_mail
from django.test import SimpleTestCase, override_settings

from .email_backends import BREVO_SEND_URL, BrevoEmailBackend, BrevoError

BACKEND = "Apps.Contact_App.email_backends.BrevoEmailBackend"


class FakeResponse:
    def __init__(self, status_code=201, text='{"messageId":"<1@brevo>"}'):
        self.status_code = status_code
        self.text = text


@override_settings(
    EMAIL_BACKEND=BACKEND,
    BREVO_API_KEY="xkeysib-test",
    DEFAULT_FROM_EMAIL="me@example.com",
    DEFAULT_FROM_NAME="My Portfolio",
)
class BrevoBackendTests(SimpleTestCase):
    def patch_post(self, response=None):
        return mock.patch("requests.Session.post", return_value=response or FakeResponse())

    def test_send_mail_posts_to_brevo_api(self):
        with self.patch_post() as post:
            sent = send_mail("Hello", "Plain body", None, ["you@example.com"])
        self.assertEqual(sent, 1)
        url = post.call_args.args[0]
        kwargs = post.call_args.kwargs
        self.assertEqual(url, BREVO_SEND_URL)
        self.assertEqual(kwargs["headers"]["api-key"], "xkeysib-test")
        payload = kwargs["json"]
        self.assertEqual(payload["sender"], {"email": "me@example.com", "name": "My Portfolio"})
        self.assertEqual(payload["to"], [{"email": "you@example.com"}])
        self.assertEqual(payload["subject"], "Hello")
        self.assertEqual(payload["textContent"], "Plain body")
        self.assertNotIn("htmlContent", payload)
        self.assertIn("timeout", kwargs)

    def test_html_cc_bcc_reply_to_and_attachments(self):
        msg = EmailMultiAlternatives(
            "Subj", "text", "Hari <hari@example.com>", ["Bob <bob@example.com>"],
            cc=["cc@example.com"], bcc=["bcc@example.com"], reply_to=["reply@example.com"],
        )
        msg.attach_alternative("<b>html</b>", "text/html")
        msg.attach("cv.pdf", b"%PDF", "application/pdf")
        with self.patch_post() as post:
            self.assertEqual(get_connection().send_messages([msg]), 1)
        payload = post.call_args.kwargs["json"]
        self.assertEqual(payload["sender"], {"email": "hari@example.com", "name": "Hari"})
        self.assertEqual(payload["to"], [{"email": "bob@example.com", "name": "Bob"}])
        self.assertEqual(payload["cc"], [{"email": "cc@example.com"}])
        self.assertEqual(payload["bcc"], [{"email": "bcc@example.com"}])
        self.assertEqual(payload["replyTo"], {"email": "reply@example.com"})
        self.assertEqual(payload["htmlContent"], "<b>html</b>")
        self.assertEqual(payload["attachment"], [{"name": "cv.pdf", "content": base64.b64encode(b"%PDF").decode()}])

    def test_api_error_raises_unless_fail_silently(self):
        with self.patch_post(FakeResponse(401, '{"message":"Key not found"}')):
            with self.assertRaises(BrevoError):
                send_mail("x", "y", None, ["you@example.com"])
            self.assertEqual(send_mail("x", "y", None, ["you@example.com"], fail_silently=True), 0)

    @override_settings(BREVO_API_KEY="")
    def test_missing_key(self):
        with self.assertRaises(BrevoError):
            BrevoEmailBackend().send_messages([EmailMultiAlternatives("s", "b", None, ["a@b.c"])])
        self.assertEqual(BrevoEmailBackend(fail_silently=True).send_messages(
            [EmailMultiAlternatives("s", "b", None, ["a@b.c"])]), 0)

    def test_no_recipients_or_messages(self):
        with self.patch_post() as post:
            self.assertEqual(BrevoEmailBackend().send_messages([]), 0)
            self.assertEqual(BrevoEmailBackend().send_messages([EmailMultiAlternatives("s", "b", None, [])]), 0)
        post.assert_not_called()
