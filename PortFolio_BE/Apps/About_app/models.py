from django.db import models
from datetime import date

class AboutMe(models.Model):
    name = models.CharField(max_length=100)
    phone_number = models.CharField(max_length=20)
    experience = models.CharField(
        max_length=20,
        help_text="Total experience in years/months",
        default="0 months",
        editable=False
    )
    linkedin_id = models.URLField()
    nationality = models.CharField(max_length=50)
    email = models.EmailField()
    is_freelance_available = models.BooleanField(default=False)

    def __str__(self):
        return self.name

    def calculate_experience(self):
        experiences = Experience.objects.all()

        total_days = 0
        today = date.today()

        for exp in experiences:
            end_date = exp.end_date if exp.end_date else today
            delta = end_date - exp.start_date
            total_days += delta.days

        # Calculate total months (more precise than days/30)
        total_months = total_days * 12 / 365.25  # Using 365.25 to account for leap years

        if total_months < 1:
            return "0 months"
        elif total_months < 12:
            # For less than 1 year, show months
            months = round(total_months)
            return f"{months} month{'s' if months > 1 else ''}"
        else:
            # For 1 year or more, show years with decimal
            years = round(total_months / 12, 1)
            return f"{years} year{'s' if years > 1 else ''}"
        
    def save(self, *args, **kwargs):
        # Update experience field before saving
        self.experience = self.calculate_experience()
        super().save(*args, **kwargs)
    
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
    
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Update AboutMe experience whenever an Experience is saved
        about_me = AboutMe.objects.first()
        if about_me:
            about_me.save()
    
    def delete(self, *args, **kwargs):
        super().delete(*args, **kwargs)
        # Update AboutMe experience whenever an Experience is deleted
        about_me = AboutMe.objects.first()
        if about_me:
            about_me.save()
                        
class Education(models.Model):
    degree = models.CharField(max_length=100)
    institution = models.CharField(max_length=100)
    start_year = models.IntegerField()
    end_year = models.IntegerField()
    description = models.TextField(blank=True)

    def __str__(self):
        return f"{self.degree} from {self.institution}"
