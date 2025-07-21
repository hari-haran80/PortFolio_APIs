from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Profile
from django.conf import settings

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'password', 'first_name', 'last_name', 'email', 'is_superuser']
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        return User.objects.create_user(**validated_data)

class ProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer()
    uploaded_image = serializers.ImageField(write_only=True, required=False)
    profile_picture = serializers.SerializerMethodField()

    class Meta:
        model = Profile
        fields = ['user', 'gender', 'position', 'phone_number', 'uploaded_image', 'profile_picture']

    def get_profile_picture(self, obj):
        if obj.profile_picture:
            return obj.profile_picture.url
        return settings.DEFAULT_PROFILE_PICTURE_URL

    def create(self, validated_data):
        user_data = validated_data.pop('user')
        image = validated_data.pop('uploaded_image', None)

        user = User.objects.create_user(**user_data)
        profile = Profile(user=user, **validated_data)

        if image:
            profile.profile_picture = image
            profile.save()

        return profile

    def update(self, instance, validated_data):
        user_data = validated_data.pop('user', None)
        image = validated_data.pop('uploaded_image', None)

        if user_data:
            user = instance.user
            for attr, value in user_data.items():
                if attr == 'password':
                    user.set_password(value)
                else:
                    setattr(user, attr, value)
            user.save()

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        if image:
            instance.profile_picture = image

        instance.save()
        return instance