from django.urls import path
from .views import ResumeUploadView, ResumeDownloadView

urlpatterns = [
    path('upload/', ResumeUploadView.as_view(), name='resume-upload'),
    path('download/', ResumeDownloadView.as_view(), name='resume-download'),
]