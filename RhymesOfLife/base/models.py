from django.db import models
from django.contrib.auth.models import User


class AdditionalUserInfo(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='additional_info')

    # Basic info
    first_name = models.CharField(max_length=128, blank=True, null=True, default=None)
    last_name = models.CharField(max_length=128, blank=True, null=True, default=None)
    email = models.EmailField(blank=True, null=True, default=None)
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)

    # Medical information
    syndrome = models.CharField(max_length=255, blank=True, null=True)
    birth_date = models.DateField(blank=True, null=True)

    # Verification flags
    is_verified = models.BooleanField(default=False)
    ready_for_verification = models.BooleanField(default=False)

    # Friends management - ИСПРАВЛЕНО: убран null=True
    friends = models.ManyToManyField('self', symmetrical=True, blank=True)

    def __str__(self):
        return f"{self.user.username}'s info"
    
    def is_friends_with(self, other_user):
        return self.friends.filter(user=other_user).exists()


class MedicalExam(models.Model):
    user_info = models.ForeignKey(
        'AdditionalUserInfo',
        on_delete=models.CASCADE,
        related_name='medical_exams'
    )
    exam_date = models.DateField()
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-exam_date', '-created_at']

    def __str__(self):
        return f"Обследование от {self.exam_date.strftime('%Y-%m-%d')}"


class MedicalDocument(models.Model):
    exam = models.ForeignKey(
        MedicalExam,
        on_delete=models.CASCADE,
        related_name='documents',
        null=True,
        blank=True 
    )
    file = models.FileField(upload_to='medical_documents/')
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-uploaded_at']

    def __str__(self):
        return f"Документ {self.file.name}"


class FriendRequest(models.Model):
    from_user = models.ForeignKey(User, related_name='sent_friend_requests', on_delete=models.CASCADE)
    to_user = models.ForeignKey(User, related_name='received_friend_requests', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('from_user', 'to_user')

    def __str__(self):
        return f"{self.from_user.username} ➡️ {self.to_user.username}"


class Notification(models.Model):
    NOTIFICATION_TYPES = (
        ('FRIEND_REQUEST', 'Friend Request'),
    )

    recipient = models.ForeignKey(AdditionalUserInfo, related_name='notifications', on_delete=models.CASCADE)
    sender = models.ForeignKey(AdditionalUserInfo, related_name='sent_notifications', on_delete=models.CASCADE)
    
    notification_type = models.CharField(max_length=50, choices=NOTIFICATION_TYPES)  # ИСПРАВЛЕНО: правильное имя поля
    message = models.TextField(blank=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.notification_type} от {self.sender.user.username} -> {self.recipient.user.username}"