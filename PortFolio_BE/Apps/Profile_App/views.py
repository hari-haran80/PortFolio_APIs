from rest_framework import generics, permissions
from .models import Profile
from .serializers import ProfileSerializer
from rest_framework_simplejwt.authentication import JWTAuthentication

class ProfileListCreateView(generics.ListCreateAPIView):
    queryset = Profile.objects.all()
    serializer_class = ProfileSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]  # Changed from AllowAny for better security

class ProfileDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Profile.objects.all()
    serializer_class = ProfileSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]  # Changed from AllowAny for better security

    def perform_destroy(self, instance):
        # Delete the associated user when the profile is deleted
        instance.user.delete()
        super().perform_destroy(instance)