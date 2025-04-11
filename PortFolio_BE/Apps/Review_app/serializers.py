from rest_framework import serializers
from .models import *

class ReviewSerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField(read_only = True)
    
    class Meta:
        model = Review
        fields = '__all__'
        read_only_fields = ["user"]