"""Django email backend that sends through Brevo's transactional email HTTPS API.

Enabled automatically in settings.py when BREVO_API_KEY is set. Because it uses
HTTPS (port 443) instead of SMTP, it works on hosts that block outgoing SMTP,
such as Render's free instances. All existing `send_mail(...)` calls use it
without any code changes.

Docs: https://developers.brevo.com/reference/sendtransacemail
"""
import base64
import logging
from email.utils import parseaddr

import requests
from django.conf import settings
from django.core.mail.backends.base import BaseEmailBackend

logger = logging.getLogger(__name__)

BREVO_SEND_URL = "https://api.brevo.com/v3/smtp/email"
BREVO_TIMEOUT = 15  # seconds


class BrevoError(Exception):
    pass


def _contact(address):
    """'Name <a@b.c>' or 'a@b.c' -> {'email': ..., 'name': ...}"""
    name, email = parseaddr(address)
    contact = {"email": email or address}
    if name:
        contact["name"] = name
    return contact


class BrevoEmailBackend(BaseEmailBackend):
    def __init__(self, api_key=None, fail_silently=False, **kwargs):
        super().__init__(fail_silently=fail_silently, **kwargs)
        self.api_key = api_key or getattr(settings, "BREVO_API_KEY", "")
        self.session = None

    def open(self):
        if self.session is None:
            self.session = requests.Session()
            return True
        return False

    def close(self):
        if self.session is not None:
            self.session.close()
            self.session = None

    def build_payload(self, message):
        from_name, from_email = parseaddr(message.from_email or settings.DEFAULT_FROM_EMAIL)
        sender = {
            "email": from_email or settings.DEFAULT_FROM_EMAIL,
            "name": from_name or getattr(settings, "DEFAULT_FROM_NAME", "") or from_email,
        }
        payload = {
            "sender": sender,
            "to": [_contact(a) for a in message.to],
            "subject": message.subject or "(no subject)",
        }
        if message.cc:
            payload["cc"] = [_contact(a) for a in message.cc]
        if message.bcc:
            payload["bcc"] = [_contact(a) for a in message.bcc]
        if message.reply_to:
            payload["replyTo"] = _contact(message.reply_to[0])

        html = None
        for content, mimetype in getattr(message, "alternatives", []) or []:
            if mimetype == "text/html":
                html = content
        if message.content_subtype == "html":
            html = message.body
        else:
            payload["textContent"] = message.body or " "
        if html:
            payload["htmlContent"] = html

        attachments = []
        for attachment in message.attachments:
            if isinstance(attachment, tuple):
                filename, content, _mimetype = attachment
                if isinstance(content, str):
                    content = content.encode()
                attachments.append({"name": filename, "content": base64.b64encode(content).decode()})
        if attachments:
            payload["attachment"] = attachments
        return payload

    def _send(self, message):
        if not message.recipients():
            return False
        response = self.session.post(
            BREVO_SEND_URL,
            json=self.build_payload(message),
            headers={
                "api-key": self.api_key,
                "accept": "application/json",
                "content-type": "application/json",
            },
            timeout=BREVO_TIMEOUT,
        )
        if response.status_code not in (200, 201, 202):
            raise BrevoError(f"Brevo API error {response.status_code}: {response.text[:300]}")
        return True

    def send_messages(self, email_messages):
        if not email_messages:
            return 0
        if not self.api_key:
            if self.fail_silently:
                return 0
            raise BrevoError("BREVO_API_KEY is not configured")

        new_session = self.open()
        sent = 0
        try:
            for message in email_messages:
                try:
                    if self._send(message):
                        sent += 1
                except Exception:
                    logger.exception("Brevo failed to send email to %s", message.to)
                    if not self.fail_silently:
                        raise
        finally:
            if new_session:
                self.close()
        return sent
