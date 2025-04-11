from django.db import models

class AboutMe(models.Model):
    name = models.CharField(max_length=100)
    phone_number = models.CharField(max_length=20)
    experience = models.PositiveIntegerField(help_text="Total years of experience")
    linkedin_id = models.URLField()
    nationality = models.CharField(max_length=50)
    email = models.EmailField()
    is_freelance_available = models.BooleanField(default=False)

    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name = "About Me"
        verbose_name_plural = "About Me"

class Language(models.Model):
    about_me = models.ForeignKey(AboutMe, related_name='languages', on_delete=models.CASCADE)
    name = models.CharField(max_length=50)
    level = models.CharField(max_length=50)

    def __str__(self):
        return f"{self.name} ({self.level})"

class Experience(models.Model):
    title = models.CharField(max_length=100)
    company = models.CharField(max_length=100)
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    description = models.TextField(blank=True)

    def __str__(self):
        return f"{self.title} at {self.company}"

class Education(models.Model):
    degree = models.CharField(max_length=100)
    institution = models.CharField(max_length=100)
    start_year = models.IntegerField()
    end_year = models.IntegerField()
    description = models.TextField(blank=True)

    def __str__(self):
        return f"{self.degree} from {self.institution}"
