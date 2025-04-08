from rest_framework import generics
from .models import Contact
from .serializers import ContactSerializer
from django.core.mail import send_mail
from django.conf import settings

# Create a new contact entry
class ContactCreateView(generics.CreateAPIView):

    permission_classes = []

    queryset = Contact.objects.all()
    serializer_class = ContactSerializer

    def perform_create(self, serializer):
        # Save the contact form data
        contact = serializer.save()

        # Send email to the user
        user_subject = 'Contact Form Submitted Successfully'
        user_message = f"Dear {contact.first_name} {contact.last_name},\n\nThank you for contacting us. We have received your message and our team will get back to you as soon as possible.\n\nBest regards,\nYour Company Name"
        user_from_email = settings.DEFAULT_FROM_EMAIL
        user_to_email = [contact.email]

        send_mail(user_subject, user_message, user_from_email, user_to_email, fail_silently=False)

        # Send email to the admin
        admin_subject = 'New Contact Form Submission'
        admin_message = f"A new contact form has been submitted:\n\nName: {contact.first_name} {contact.last_name}\nEmail: {contact.email}\nPhone: {contact.phone_number}\nSubject: {contact.subject}\nMessage: {contact.message}\n\nSubmitted on: {contact.created_at}"
        admin_from_email = settings.DEFAULT_FROM_EMAIL
        admin_to_email = [settings.ADMIN_EMAIL]  # Make sure to set ADMIN_EMAIL in your settings.py

        send_mail(admin_subject, admin_message, admin_from_email, admin_to_email, fail_silently=False)


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
    