from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Profile
from cryptography.fernet import Fernet
from django.conf import settings

cipher_suite = Fernet(settings.ENCRYPTION_KEY)

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

    class Meta:
        model = Profile
        fields = ['user', 'gender', 'position', 'phone_number', 'uploaded_image']

    def to_representation(self, instance):
        data = super().to_representation(instance)
        decrypted = instance.get_decrypted_profile_picture()
        if decrypted:
            import base64
            data['profile_picture'] = f"data:{instance.image_type};base64," + base64.b64encode(decrypted).decode()
        else:
            data['profile_picture'] = None
        return data

    def create(self, validated_data):
        user_data = validated_data.pop('user')
        image = validated_data.pop('uploaded_image', None)

        user = User.objects.create_user(**user_data)

        profile = Profile(user=user, **validated_data)

        if image:
            binary_data = image.read()
            profile.profile_picture = cipher_suite.encrypt(binary_data)
            profile.image_type = image.content_type

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
            binary_data = image.read()
            instance.profile_picture = cipher_suite.encrypt(binary_data)
            instance.image_type = image.content_type

        instance.save()
        return instance