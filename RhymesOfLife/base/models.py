from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver


class AdditionalUserInfo(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='additional_info')
    syndrome = models.CharField(max_length=255, blank=True, null=True)
    birth_date = models.DateField(blank=True, null=True)
    is_verified = models.BooleanField(default=False)
    ready_for_verification = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.user.username}'s info"


@receiver(post_save, sender=User)
def create_additional_user_info(sender, instance, created, **kwargs):
    if created:
        AdditionalUserInfo.objects.create(user=instance)


@receiver(post_save, sender=User)
def save_additional_user_info(sender, instance, **kwargs):
    instance.additional_info.save()
