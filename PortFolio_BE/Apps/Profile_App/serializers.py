from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Profile
import base64
from cryptography.fernet import Fernet
from django.conf import settings

# Initialize cipher with the encryption key from settings
cipher_suite = Fernet(settings.ENCRYPTION_KEY)

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'password', 'first_name', 'last_name', 'email', 'is_superuser']
        extra_kwargs = {'password': {'write_only': True}}

    def validate_username(self, value):
        if self.instance and self.instance.username == value:
            return value
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError("A user with that username already exists.")
        return value

    def create(self, validated_data):
        user = User.objects.create_user(**validated_data)
        return user

class ProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer()
    profile_picture = serializers.CharField(required=False, allow_null=True)

    class Meta:
        model = Profile
        fields = ['user', 'profile_picture', 'gender', 'position', 'phone_number']

    def to_representation(self, instance):
        """
        Convert the decrypted binary profile picture data to a Base64-encoded string for output.
        """
        representation = super().to_representation(instance)
        decrypted_picture = instance.get_decrypted_profile_picture()
        if decrypted_picture:
            representation['profile_picture'] = base64.b64encode(decrypted_picture).decode('utf-8')
        else:
            representation['profile_picture'] = None
        return representation

    def to_internal_value(self, data):
        """
        Convert the Base64-encoded profile picture string to binary data and encrypt it for storage.
        """
        internal_value = super().to_internal_value(data)
        profile_picture_base64 = data.get('profile_picture')
    
        if profile_picture_base64:
            try:
                # Remove the "data:image/jpeg;base64," prefix if present
                if profile_picture_base64.startswith('data:image'):
                    profile_picture_base64 = profile_picture_base64.split(',')[1]
                # Decode the Base64 string to binary data
                binary_data = base64.b64decode(profile_picture_base64)
                # Encrypt the binary data
                internal_value['profile_picture'] = cipher_suite.encrypt(binary_data)
            except Exception as e:
                raise serializers.ValidationError({"profile_picture": "Invalid Base64 encoding or encryption failed."})
        else:
            internal_value['profile_picture'] = None
    
        return internal_value
    
    def create(self, validated_data):
        user_data = validated_data.pop('user')
        user = User.objects.create_user(**user_data)
        profile = Profile.objects.create(user=user, **validated_data)
        return profile

    def update(self, instance, validated_data):
        user_data = validated_data.pop('user', None)
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
        instance.save()
        
        return instance