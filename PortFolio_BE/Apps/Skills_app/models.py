from django.db import models
from cloudinary.models import CloudinaryField

class SkillCategory(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name


class Skill(models.Model):
    category = models.ForeignKey(SkillCategory, on_delete=models.CASCADE, related_name='skills')
    name = models.CharField(max_length=100)
    fluency = models.PositiveIntegerField()
    image = CloudinaryField('image', blank=True, null=True)  # Cloudinary field
    years_of_experience = models.DecimalField(max_digits=4, decimal_places=1, blank=True, null=True)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.name} ({self.fluency}%)"
