from django.conf import settings
from django.contrib.auth.models import User
from rest_framework import serializers

from .models import Profile

MAX_IMAGE_SIZE = 5 * 1024 * 1024  # 5 MB


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'password', 'first_name', 'last_name', 'email', 'is_superuser', 'last_login']
        extra_kwargs = {
            'password': {'write_only': True},
            'last_login': {'read_only': True},
            # Uniqueness is checked in ProfileSerializer.validate, where the
            # current user is known (the nested serializer has no instance and
            # would otherwise reject a user's own, unchanged username).
            'username': {'validators': []},
        }

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

    def validate_uploaded_image(self, image):
        if image and image.size > MAX_IMAGE_SIZE:
            raise serializers.ValidationError("Image must be 5 MB or smaller.")
        return image

    def _request_user_is_superuser(self):
        request = self.context.get('request')
        return bool(request and request.user and request.user.is_superuser)

    def validate(self, attrs):
        user_data = attrs.get('user') or {}

        # Only superusers may grant or revoke superuser status.
        if 'is_superuser' in user_data and not self._request_user_is_superuser():
            user_data.pop('is_superuser')

        current_user = self.instance.user if self.instance else None
        username = user_data.get('username')
        if username:
            qs = User.objects.filter(username__iexact=username)
            if current_user:
                qs = qs.exclude(pk=current_user.pk)
            if qs.exists():
                raise serializers.ValidationError({'user': {'username': ['A user with that username already exists.']}})

        email = user_data.get('email')
        if email:
            qs = User.objects.filter(email__iexact=email)
            if current_user:
                qs = qs.exclude(pk=current_user.pk)
            if qs.exists():
                raise serializers.ValidationError({'user': {'email': ['A user with that email already exists.']}})

        return attrs

    def create(self, validated_data):
        user_data = validated_data.pop('user')
        image = validated_data.pop('uploaded_image', None)

        user = User.objects.create_user(**user_data)
        # The post_save signal already created an empty profile for this user.
        profile = user.profile
        for attr, value in validated_data.items():
            setattr(profile, attr, value)
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
                    if value:
                        user.set_password(value)
                elif attr == 'last_login':
                    continue  # managed by auth events, not client updates
                else:
                    setattr(user, attr, value)
            if 'is_superuser' in user_data:
                user.is_staff = user_data['is_superuser']
            user.save()

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        if image:
            instance.profile_picture = image

        instance.save()
        return instance
