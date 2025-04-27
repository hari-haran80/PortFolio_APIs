from rest_framework import serializers
from .models import AboutMe, Language, Experience, Education

class LanguageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Language
        fields = '__all__'

class AboutMeSerializer(serializers.ModelSerializer):
    languages = LanguageSerializer(many=True, read_only=True)
    # Add this to ensure the experience field is included in responses
    experience = serializers.CharField(read_only=True)

    class Meta:
        model = AboutMe
        fields = '__all__'

class ExperienceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Experience
        fields = '__all__'

class EducationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Education
        fields = '__all__'
