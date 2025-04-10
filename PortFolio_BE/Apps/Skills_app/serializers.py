from rest_framework import serializers
from .models import Skill, SkillCategory
import base64

class SkillSerializer(serializers.ModelSerializer):
    image_base64 = serializers.SerializerMethodField()  # read-only image
    uploaded_image = serializers.ImageField(write_only=True, required=False)  # for uploading image

    class Meta:
        model = Skill
        fields = [
            'id', 'category', 'name', 'fluency',
            'image_base64', 'uploaded_image', 'image_type',
            'years_of_experience', 'description'
        ]

    def get_image_base64(self, obj):
        if obj.image_data:
            return f"data:{obj.image_type};base64,{base64.b64encode(obj.image_data).decode()}"
        return None

    def create(self, validated_data):
        image = validated_data.pop('uploaded_image', None)
        if image:
            validated_data['image_data'] = image.read()
            validated_data['image_type'] = image.content_type
        return super().create(validated_data)

    def update(self, instance, validated_data):
        image = validated_data.pop('uploaded_image', None)
        if image:
            instance.image_data = image.read()
            instance.image_type = image.content_type
        return super().update(instance, validated_data)

class SkillCategorySerializer(serializers.ModelSerializer):
    skills = SkillSerializer(many=True, read_only=True)

    class Meta:
        model = SkillCategory
        fields = ['id', 'name', 'description', 'skills']
