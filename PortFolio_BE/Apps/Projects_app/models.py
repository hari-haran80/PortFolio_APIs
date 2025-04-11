from django.db import models
from base64 import b64encode, b64decode
from cryptography.fernet import Fernet
from django.conf import settings

def get_cipher():
    return Fernet(settings.ENCRYPTION_KEY)

class Project(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField()
    tech_stack = models.TextField()
    live_link = models.URLField(blank=True, null=True)
    repo_link = models.URLField(blank=True, null=True)
    image = models.BinaryField(blank=True, null=True, editable=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def set_encrypted_image(self, raw_file):
        encrypted = get_cipher().encrypt(raw_file.read())
        self.image = encrypted

    def get_decrypted_image_base64(self):
        if self.image:
            decrypted = get_cipher().decrypt(self.image)
            return b64encode(decrypted).decode('utf-8')
        return None

    def __str__(self):
        return self.title
