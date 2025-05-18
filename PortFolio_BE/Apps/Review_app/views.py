from rest_framework import generics, permissions, serializers
from django.db import IntegrityError
from .models import Review
from .serializers import ReviewSerializer
from .permissions import IsOwnerOrSuperUser
from django.core.mail import send_mail
from django.conf import settings

class ReviewListCreateView(generics.ListCreateAPIView):
    queryset = Review.objects.all()
    serializer_class = ReviewSerializer

    def get_permissions(self):
        if self.request.method == 'POST':
            return [permissions.IsAuthenticated()]
        return [permissions.AllowAny()]

    def perform_create(self, serializer):
        try:
            # Save the review first
            serializer.save(user=self.request.user)
            
            # Get the created review instance
            review = serializer.instance
            
            # Send email notification
            subject = f"New Review Received"
            message = f"""
            New review submitted by {review.user.username}:

            Content: {review.comment}
            Rating: {review.rating}/5

            Review ID: {review.id}
            Submitted at: {review.created_at}
            """
            
            send_mail(
                subject,
                message.strip(),
                settings.DEFAULT_FROM_EMAIL,
                [settings.ADMIN_EMAIL],
                fail_silently=False,
            )
            
        except IntegrityError:
            raise serializers.ValidationError("Review already exists for this user.")

class ReviewDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Review.objects.all()
    serializer_class = ReviewSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrSuperUser]
