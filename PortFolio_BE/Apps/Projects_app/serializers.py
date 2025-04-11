from rest_framework import serializers
from .models import Project

class ProjectSerializer(serializers.ModelSerializer):
    image_base64 = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Project
        fields = [
            'id', 'title', 'description', 'tech_stack',
            'live_link', 'repo_link', 'image_base64',
            'created_at', 'updated_at'
        ]

    def get_image_base64(self, obj):
        base64_data = obj.get_decrypted_image_base64()
        if base64_data:
            return f"data:image/jpeg;base64,{base64_data}"
        return None
