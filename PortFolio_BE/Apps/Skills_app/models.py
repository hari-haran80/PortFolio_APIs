from django.db import models

class SkillCategory(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name


class Skill(models.Model):
    category = models.ForeignKey(SkillCategory, on_delete=models.CASCADE, related_name='skills')
    name = models.CharField(max_length=100)
    fluency = models.PositiveIntegerField()
    image_data = models.BinaryField(blank=True, null=True)  # 🟢 binary image data
    image_type = models.CharField(max_length=50, blank=True, null=True)  # e.g., 'image/png'
    years_of_experience = models.DecimalField(max_digits=4, decimal_places=1, blank=True, null=True)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.name} ({self.fluency}%)"
