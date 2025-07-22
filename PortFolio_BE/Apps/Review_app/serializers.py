from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Review
from django.conf import settings

class UserProfileSerializer(serializers.ModelSerializer):
    profile_picture = serializers.SerializerMethodField()
    position = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name', 'profile_picture', 'position']

    def get_profile_picture(self, obj):
        if hasattr(obj, 'profile'):
            profile = obj.profile
            if profile.profile_picture:
                return profile.profile_picture.url
        return settings.DEFAULT_PROFILE_PICTURE_URL

    def get_position(self, obj):
        if hasattr(obj, 'profile'):
            return obj.profile.position
        return None

class ReviewSerializer(serializers.ModelSerializer):
    user = UserProfileSerializer(read_only=True)
    
    class Meta:
        model = Review
        fields = '__all__'
        read_only_fields = ["user"]