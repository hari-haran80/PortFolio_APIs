from rest_framework import generics, permissions
from rest_framework_simplejwt.authentication import JWTAuthentication

from Apps.Authentication_App.permissions import IsSuperUser
from .models import Profile
from .serializers import ProfileSerializer


class IsProfileOwnerOrSuperUser(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        return obj.user_id == request.user.id or request.user.is_superuser


class ProfileListCreateView(generics.ListCreateAPIView):
    """Admin only: lists every user's profile (emails etc.)."""
    queryset = Profile.objects.select_related("user").order_by("user_id")
    serializer_class = ProfileSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsSuperUser]


class ProfileDetailView(generics.RetrieveUpdateDestroyAPIView):
    """A user can view/edit/delete their own profile; superusers can manage any profile.

    The URL id is the *user* id (the FE only knows user ids: the serializer exposes
    `user.id`, and login returns `user_id`).
    """
    queryset = Profile.objects.select_related("user")
    serializer_class = ProfileSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [permissions.IsAuthenticated, IsProfileOwnerOrSuperUser]
    lookup_field = "user_id"
    lookup_url_kwarg = "pk"

    def perform_destroy(self, instance):
        # Deleting the user cascades to the profile.
        instance.user.delete()
