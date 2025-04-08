from django.db import models
from django.conf import settings
from cryptography.fernet import Fernet
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

cipher = Fernet(settings.ENCRYPTION_KEY)

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    profile_picture = models.BinaryField(blank=True, null=True)  # Store encrypted binary data
    GENDER_CHOICES = [
        ('M', 'Male'),
        ('F', 'Female'),
        ('O', 'Other'),
    ]
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES, default='O')
    position = models.CharField(max_length=100, default='Employee')
    phone_number = models.CharField(max_length=15, default='+1234567890')

    def __str__(self):
        return f'{self.user.first_name} {self.user.last_name}'

    class Meta:
        db_table = "User_Profile"
        
    def __str__(self):
        return self.user.username
        
    def save(self, *args, **kwargs):
        if self.profile_picture and isinstance(self.profile_picture, bytes) and not self.profile_picture.startswith(b'gAAAAA'):
            # Encrypt only if not already encrypted
            self.profile_picture = cipher.encrypt(self.profile_picture)
        super().save(*args, **kwargs)

    def get_decrypted_profile_picture(self):
        """Decrypt the profile picture for retrieval"""
        if self.profile_picture and self.profile_picture.startswith(b'gAAAAA'):
            return cipher.decrypt(self.profile_picture)
        return None


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    if hasattr(instance, 'profile'):
        instance.profile.save()
