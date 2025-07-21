from django.db import models
from django.conf import settings
from cryptography.fernet import Fernet
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

cipher_suite = Fernet(settings.ENCRYPTION_KEY)

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    profile_picture = models.BinaryField(blank=True, null=True)
    image_type = models.CharField(max_length=50, blank=True, null=True)  # To store MIME type (like image/png)

    GENDER_CHOICES = [('M', 'Male'), ('F', 'Female'), ('O', 'Other')]
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES, default='O')
    position = models.CharField(max_length=100, default='Employee')
    phone_number = models.CharField(max_length=15, default='+1234567890')

    def __str__(self):
        return f'{self.user.first_name} {self.user.last_name}'

    class Meta:
        db_table = "User_Profile"

    def save(self, *args, **kwargs):
        if self.profile_picture:
            data = bytes(self.profile_picture) if isinstance(self.profile_picture, memoryview) else self.profile_picture
            if not data.startswith(b'gAAAAA'):
                self.profile_picture = cipher_suite.encrypt(data)
        super().save(*args, **kwargs)

    def get_decrypted_profile_picture(self):
        if self.profile_picture:
            data = bytes(self.profile_picture) if isinstance(self.profile_picture, memoryview) else self.profile_picture
            if data.startswith(b'gAAAAA'):
                try:
                    return cipher_suite.decrypt(data)
                except:
                    return None
            return data
        return None


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    if hasattr(instance, 'profile'):
        instance.profile.save()
