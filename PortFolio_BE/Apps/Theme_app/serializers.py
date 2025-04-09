from rest_framework import serializers
from .models import UserTheme

class UserThemeSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserTheme
        fields = ['theme']
