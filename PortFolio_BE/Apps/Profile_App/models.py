from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from cloudinary.models import CloudinaryField
from django.conf import settings

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    profile_picture = CloudinaryField(
        'image', 
        max_length=255, 
        blank=True, 
        null=True,
        default=settings.DEFAULT_PROFILE_PICTURE_URL
    )

    GENDER_CHOICES = [('M', 'Male'), ('F', 'Female'), ('O', 'Other')]
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES, default='O')
    position = models.CharField(max_length=100, default='Employee')
    phone_number = models.CharField(max_length=15, default='+1234567890')

    def __str__(self):
        return f'{self.user.first_name} {self.user.last_name}'

    class Meta:
        db_table = "User_Profile"

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    if hasattr(instance, 'profile'):
        instance.profile.save()