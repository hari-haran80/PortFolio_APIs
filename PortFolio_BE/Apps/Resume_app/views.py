import os

from django.http import FileResponse
from rest_framework import generics, status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from Apps.Authentication_App.permissions import IsSuperUser
from .models import Resume
from .serializers import ResumeSerializer

ALLOWED_RESUME_EXTENSIONS = {".pdf", ".doc", ".docx"}
MAX_RESUME_SIZE = 10 * 1024 * 1024  # 10 MB


class ResumeUploadView(generics.CreateAPIView):
    """Admin only: replaces the single stored resume."""
    queryset = Resume.objects.all()
    serializer_class = ResumeSerializer
    permission_classes = [IsSuperUser]

    def create(self, request, *args, **kwargs):
        file = request.FILES.get('file')
        if not file:
            return Response({'error': 'No file uploaded'}, status=status.HTTP_400_BAD_REQUEST)

        ext = os.path.splitext(file.name)[1].lower()
        if ext not in ALLOWED_RESUME_EXTENSIONS:
            return Response(
                {'error': 'Only PDF, DOC or DOCX files are allowed'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if file.size > MAX_RESUME_SIZE:
            return Response({'error': 'File is larger than 10 MB'}, status=status.HTTP_400_BAD_REQUEST)

        serializer = self.get_serializer(data={'file': file})
        serializer.is_valid(raise_exception=True)

        # Only delete the old resume once the new one is known to be valid.
        for old in Resume.objects.all():
            old.file.delete(save=False)
            old.delete()
        serializer.save()

        return Response(serializer.data, status=status.HTTP_201_CREATED)


class ResumeDownloadView(generics.GenericAPIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def get(self, request, *args, **kwargs):
        resume = Resume.objects.order_by('-uploaded_at').first()
        if not resume:
            return Response({'error': 'Resume not found'}, status=status.HTTP_404_NOT_FOUND)

        try:
            file_handle = resume.file.open('rb')
        except (FileNotFoundError, OSError):
            return Response({'error': 'Resume file is missing'}, status=status.HTTP_404_NOT_FOUND)

        return FileResponse(
            file_handle,
            as_attachment=True,
            filename=os.path.basename(resume.file.name),
        )
