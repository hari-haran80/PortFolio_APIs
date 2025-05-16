from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Review

class UserProfileSerializer(serializers.ModelSerializer):
    profile_picture = serializers.SerializerMethodField()
    position = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name', 'profile_picture', 'position']

    def get_profile_picture(self, obj):
        if hasattr(obj, 'profile'):
            profile = obj.profile
            decrypted = profile.get_decrypted_profile_picture()
            if decrypted:
                import base64
                return f"data:{profile.image_type};base64," + base64.b64encode(decrypted).decode()
        return None

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