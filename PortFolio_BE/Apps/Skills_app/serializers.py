from rest_framework import serializers
from .models import Skill, SkillCategory

class SkillSerializer(serializers.ModelSerializer):
    image_url = serializers.SerializerMethodField()
    # FileField so SVG icons are allowed; validate_uploaded_image limits it to images.
    uploaded_image = serializers.FileField(write_only=True, required=False, allow_null=True)
    fluency = serializers.IntegerField(min_value=0, max_value=100)

    class Meta:
        model = Skill
        fields = [
            'id', 'category', 'name', 'fluency',
            'image_url', 'uploaded_image',
            'years_of_experience', 'description'
        ]
        read_only_fields = ['image_url']
        
    ALLOWED_IMAGE_EXTENSIONS = ('.png', '.jpg', '.jpeg', '.gif', '.webp', '.svg')
    MAX_IMAGE_SIZE = 5 * 1024 * 1024

    def validate_uploaded_image(self, file):
        if not file:
            return file
        if not file.name.lower().endswith(self.ALLOWED_IMAGE_EXTENSIONS):
            raise serializers.ValidationError("Upload a PNG, JPG, GIF, WEBP or SVG image.")
        if file.size > self.MAX_IMAGE_SIZE:
            raise serializers.ValidationError("Image must be 5 MB or smaller.")
        return file

    def get_image_url(self, obj):
        if obj.image:
            return obj.image.url
        return None

    def create(self, validated_data):
        image = validated_data.pop('uploaded_image', None)
        skill = super().create(validated_data)
        
        if image:
            skill.image = image
            skill.save()
            
        return skill

    def update(self, instance, validated_data):
        image = validated_data.pop('uploaded_image', None)
        
        if image is False:
            instance.image = None
        elif image:
            instance.image = image
            
        return super().update(instance, validated_data)

class SkillCategorySerializer(serializers.ModelSerializer):
    skills = SkillSerializer(many=True, read_only=True)

    class Meta:
        model = SkillCategory
        fields = ['id', 'name', 'description', 'skills']
