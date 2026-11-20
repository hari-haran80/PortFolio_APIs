import logging

from django.conf import settings
from django.core.mail import send_mail
from django.db import IntegrityError, transaction
from rest_framework import generics, permissions, serializers

from .models import Review
from .permissions import IsOwnerOrSuperUser
from .serializers import ReviewSerializer

logger = logging.getLogger(__name__)


class ReviewListCreateView(generics.ListCreateAPIView):
    queryset = Review.objects.select_related("user__profile")
    serializer_class = ReviewSerializer

    def get_permissions(self):
        if self.request.method == 'POST':
            return [permissions.IsAuthenticated()]
        return [permissions.AllowAny()]

    def perform_create(self, serializer):
        if Review.objects.filter(user=self.request.user).exists():
            raise serializers.ValidationError({"detail": "You have already submitted a review."})
        try:
            with transaction.atomic():
                review = serializer.save(user=self.request.user)
        except IntegrityError:
            raise serializers.ValidationError({"detail": "You have already submitted a review."})

        try:
            send_mail(
                "New Review Received",
                (
                    f"New review submitted by {review.user.username}:\n\n"
                    f"Content: {review.comment}\n"
                    f"Rating: {review.rating}/5\n\n"
                    f"Review ID: {review.id}\n"
                    f"Submitted at: {review.created_at}"
                ),
                settings.DEFAULT_FROM_EMAIL,
                [settings.ADMIN_EMAIL],
                fail_silently=False,
            )
        except Exception:
            # The review is saved; a mail outage must not turn this into a 500.
            logger.exception("Failed to send new-review notification")


class ReviewDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Review.objects.select_related("user__profile")
    serializer_class = ReviewSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrSuperUser]
