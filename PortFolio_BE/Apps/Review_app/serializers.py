from django.conf import settings
from django.contrib.auth.models import User
from rest_framework import serializers

from .models import Review


class UserProfileSerializer(serializers.ModelSerializer):
    profile_picture = serializers.SerializerMethodField()
    position = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name', 'profile_picture', 'position']

    def get_profile_picture(self, obj):
        profile = getattr(obj, 'profile', None)
        if profile and profile.profile_picture:
            return profile.profile_picture.url
        return settings.DEFAULT_PROFILE_PICTURE_URL

    def get_position(self, obj):
        profile = getattr(obj, 'profile', None)
        return profile.position if profile else None


class ReviewSerializer(serializers.ModelSerializer):
    user = UserProfileSerializer(read_only=True)
    rating = serializers.IntegerField(min_value=1, max_value=5)
    comment = serializers.CharField(max_length=2000, trim_whitespace=True)

    class Meta:
        model = Review
        fields = '__all__'
        read_only_fields = ["user", "created_at"]
