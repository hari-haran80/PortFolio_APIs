from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError
from .models import Contact
from .serializers import ContactSerializer
from django.core.mail import send_mail
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

class ContactCreateView(generics.CreateAPIView):
    permission_classes = []
    queryset = Contact.objects.all()
    serializer_class = ContactSerializer

    def create(self, request, *args, **kwargs):
        try:
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            self.perform_create(serializer)
            
            # Prepare success response
            response_data = {
                'success': True,
                'status': 'created',
                'message': 'Contact form submitted successfully',
                'data': serializer.data
            }
            
            return Response(response_data, status=status.HTTP_201_CREATED)
            
        except ValidationError as e:
            logger.error(f"Validation error: {str(e)}")
            return Response({
                'success': False,
                'status': 'error',
                'message': 'Validation failed',
                'errors': e.detail
            }, status=status.HTTP_400_BAD_REQUEST)
            
        except Exception as e:
            logger.error(f"Server error: {str(e)}")
            return Response({
                'success': False,
                'status': 'error',
                'message': 'An error occurred while processing your request'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def perform_create(self, serializer):
        contact = serializer.save()
        
        # Email to user
        try:
            send_mail(
                subject='Contact Form Submitted Successfully',
                message=f"""Dear {contact.first_name} {contact.last_name},
                
Thank you for contacting us. We have received your message and our team will get back to you soon.

Your details:
- Email: {contact.email}
- Phone: {contact.phone_number or 'Not provided'}
- Subject: {contact.subject}
- Message: {contact.message}

We'll respond within 24-48 hours.

Best regards,
Your Company Team""",
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[contact.email],
                fail_silently=False
            )
        except Exception as e:
            logger.error(f"Failed to send user email: {str(e)}")

        # Email to admin
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
                fail_silently=False
            )
        except Exception as e:
            logger.error(f"Failed to send admin email: {str(e)}")

# Retrieve all contact entries
class ContactListView(generics.ListAPIView):

    permission_classes = []

    queryset = Contact.objects.all()
    serializer_class = ContactSerializer

# Retrieve, update, or delete a specific contact entry
class ContactDetailView(generics.RetrieveUpdateDestroyAPIView):

    permission_classes = []

    queryset = Contact.objects.all()
    serializer_class = ContactSerializer
    