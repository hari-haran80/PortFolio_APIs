import logging

from django.conf import settings
from django.core.mail import send_mail
from rest_framework import generics, status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle

from Apps.Authentication_App.permissions import IsSuperUser
from .models import Contact
from .serializers import ContactSerializer

logger = logging.getLogger(__name__)


class ContactCreateView(generics.CreateAPIView):
    """Public contact form. Rate limited to stop spam."""
    permission_classes = [AllowAny]
    authentication_classes = []
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "contact"
    queryset = Contact.objects.all()
    serializer_class = ContactSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            return Response({
                'success': False,
                'status': 'error',
                'message': 'Validation failed',
                'errors': serializer.errors,
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            self.perform_create(serializer)
        except Exception:
            logger.exception("Failed to save contact submission")
            return Response({
                'success': False,
                'status': 'error',
                'message': 'An error occurred while processing your request',
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response({
            'success': True,
            'status': 'created',
            'message': 'Contact form submitted successfully',
            'data': serializer.data,
        }, status=status.HTTP_201_CREATED)

    def perform_create(self, serializer):
        contact = serializer.save()

        # Email failures must never lose the submission, so they are only logged.
        try:
            send_mail(
                subject='Thanks for reaching out!',
                message=f"""Dear {contact.first_name} {contact.last_name},

Thank you for contacting me. I have received your message and will get back to you soon.

Your details:
- Email: {contact.email}
- Phone: {contact.phone_number or 'Not provided'}
- Subject: {contact.subject}
- Message: {contact.message}

I usually respond within 24-48 hours.

Best regards,
Hariharan""",
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[contact.email],
                fail_silently=False,
            )
        except Exception:
            logger.exception("Failed to send contact confirmation email")

        try:
            send_mail(
                subject=f'New Contact Submission: {contact.subject}',
                message=f"""New contact form submission:

Name: {contact.first_name} {contact.last_name}
Email: {contact.email}
Phone: {contact.phone_number or 'Not provided'}
Subject: {contact.subject}
Message:
{contact.message}

Submitted at: {contact.created_at}
""",
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[settings.ADMIN_EMAIL],
                fail_silently=False,
            )
        except Exception:
            logger.exception("Failed to send contact admin notification")


class ContactListView(generics.ListAPIView):
    """Admin only: contact submissions contain visitors' personal data."""
    permission_classes = [IsSuperUser]
    queryset = Contact.objects.order_by("-created_at")
    serializer_class = ContactSerializer


class ContactDetailView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsSuperUser]
    queryset = Contact.objects.all()
    serializer_class = ContactSerializer
