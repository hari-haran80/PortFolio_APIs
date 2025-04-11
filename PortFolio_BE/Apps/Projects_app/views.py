from rest_framework import generics, permissions, status
from rest_framework.response import Response
from .models import Project
from .serializers import ProjectSerializer

class ProjectListCreateView(generics.ListCreateAPIView):
    queryset = Project.objects.all().order_by('-created_at')
    serializer_class = ProjectSerializer

    def get_permissions(self):
        if self.request.method == 'POST':
            return [permissions.IsAdminUser()]
        return [permissions.AllowAny()]

    def perform_create(self, serializer):
        project = serializer.save()
        file = self.request.FILES.get('image')
        if file:
            project.set_encrypted_image(file)
            project.save()

class ProjectRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Project.objects.all()
    serializer_class = ProjectSerializer
    permission_classes = [permissions.IsAdminUser]

    def patch(self, request, *args, **kwargs):
        project = self.get_object()
        if 'image' in request.FILES:
            project.set_encrypted_image(request.FILES['image'])
            project.save()
        return self.partial_update(request, *args, **kwargs)
