from rest_framework import serializers

from .models import AboutMe, Language, Experience, Education


class LanguageSerializer(serializers.ModelSerializer):
    proficiency = serializers.IntegerField(min_value=0, max_value=100, required=False)

    class Meta:
        model = Language
        fields = '__all__'


class AboutMeSerializer(serializers.ModelSerializer):
    languages = LanguageSerializer(many=True, read_only=True)
    # Calculated from the Experience entries; never set by clients.
    experience = serializers.CharField(read_only=True)

    class Meta:
        model = AboutMe
        fields = '__all__'


class ExperienceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Experience
        fields = '__all__'

    def validate(self, attrs):
        start = attrs.get('start_date', getattr(self.instance, 'start_date', None))
        end = attrs.get('end_date', getattr(self.instance, 'end_date', None))
        if start and end and end < start:
            raise serializers.ValidationError({'end_date': 'End date cannot be before the start date.'})
        return attrs


class EducationSerializer(serializers.ModelSerializer):
    start_year = serializers.IntegerField(min_value=1900, max_value=2100)
    end_year = serializers.IntegerField(min_value=1900, max_value=2100)

    class Meta:
        model = Education
        fields = '__all__'

    def validate(self, attrs):
        start = attrs.get('start_year', getattr(self.instance, 'start_year', None))
        end = attrs.get('end_year', getattr(self.instance, 'end_year', None))
        if start and end and end < start:
            raise serializers.ValidationError({'end_year': 'End year cannot be before the start year.'})
        return attrs
