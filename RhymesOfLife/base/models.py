from django.db import models
from django.contrib.auth.models import User


class AdditionalUserInfo(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='additional_info')

    # Basic info
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='additional_info')
    first_name = models.CharField(max_length=128, blank=True, null=True, default=None)
    last_name = models.CharField(max_length=128, blank=True, null=True, default=None)
    email = models.EmailField(blank=True, null=True, default=None)

    # Medical information
    syndrome = models.CharField(max_length=255, blank=True, null=True)
    birth_date = models.DateField(blank=True, null=True)

    # Verification flags
    is_verified = models.BooleanField(default=False)
    ready_for_verification = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.user.username}'s info"

