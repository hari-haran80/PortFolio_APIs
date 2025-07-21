from django.db import models
from cloudinary.models import CloudinaryField

class Project(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField()
    tech_stack = models.TextField()
    live_link = models.URLField(blank=True, null=True)
    repo_link = models.URLField(blank=True, null=True)
    image = CloudinaryField('image', blank=True, null=True)  # Changed to CloudinaryField
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title
