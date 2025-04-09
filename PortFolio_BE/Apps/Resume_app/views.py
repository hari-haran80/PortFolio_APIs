from rest_framework import generics, status
from rest_framework.response import Response
from .models import Resume
from .serializers import ResumeSerializer
from django.http import FileResponse

class ResumeUploadView(generics.CreateAPIView):
    queryset = Resume.objects.all()
    serializer_class = ResumeSerializer

    def create(self, request, *args, **kwargs):
        # Delete any existing resumes (only keep one)
        Resume.objects.all().delete()
        
        file = request.FILES.get('file')
        if not file:
            return Response(
                {'error': 'No file uploaded'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Create new resume entry
        serializer = self.get_serializer(data={'file': file})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        
        return Response(serializer.data, status=status.HTTP_201_CREATED)

class ResumeDownloadView(generics.GenericAPIView):
    def get(self, request, *args, **kwargs):
        resume = Resume.objects.first()  # Get the single resume
        if not resume:
            return Response(
                {'error': 'Resume not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )
            
        file_handle = resume.file.open()
        response = FileResponse(file_handle)
        response['Content-Disposition'] = f'attachment; filename="{resume.file.name}"'
        return response