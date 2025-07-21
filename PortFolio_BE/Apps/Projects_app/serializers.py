from rest_framework import serializers
from .models import Project

class ProjectSerializer(serializers.ModelSerializer):
    image_url = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Project
        fields = [
            'id', 'title', 'description', 'tech_stack',
            'live_link', 'repo_link', 'image', 'image_url',
            'created_at', 'updated_at'
        ]
        extra_kwargs = {
            'image': {'write_only': True}  # Make image write-only
        }

    def get_image_url(self, obj):
        if obj.image:
            return obj.image.url
        return None
