from django.db import models
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.contrib.postgres.fields import ArrayField
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

User = get_user_model()


class Config(models.Model):
    key = models.CharField(max_length=64, unique=True, db_index=True)
    value = models.JSONField(default=dict, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Config"
        verbose_name_plural = "Config"

    def __str__(self):
        return f"{self.key}"

    @classmethod
    def get_list(cls, key: str, default=None):
        default = default if default is not None else []
        rec = cls.objects.filter(key=key).values_list("value", flat=True).first()
        if isinstance(rec, list):
            return rec
        return default


_DEFAULT_SYNDROME_CHOICES = [
    ["s1", "Syndrome 1"],
    ["s2", "Syndrome 2"],
    ["s3", "Syndrome 3"],
    ["s4", "Syndrome 4"],
    ["s5", "Syndrome 5"],
    ["s6", "Syndrome 6"],
]


def get_syndrome_choices():
    raw = Config.get_list("SYNDROME_CHOICES", default=_DEFAULT_SYNDROME_CHOICES)
    choices = [(c[0], c[1]) for c in raw if isinstance(c, (list, tuple)) and len(c) == 2]
    return choices or [(c[0], c[1]) for c in _DEFAULT_SYNDROME_CHOICES]


def _validate_syndromes(value_list):
    allowed = {c for c, _ in get_syndrome_choices()}
    invalid = [v for v in (value_list or []) if v not in allowed]
    if invalid:
        raise ValidationError(_("Invalid syndrome codes: %(codes)s"), params={"codes": ", ".join(invalid)})


class SoftDeleteQuerySet(models.QuerySet):
    def delete(self):
        return super().update(is_deleted=True, deleted_at=timezone.now())

    def hard_delete(self):
        return super().delete()

    def alive(self):
        return self.filter(is_deleted=False)

    def dead(self):
        return self.filter(is_deleted=True)


class SoftDeleteManager(models.Manager):
    def get_queryset(self):
        return SoftDeleteQuerySet(self.model, using=self._db).filter(is_deleted=False)

    def all_with_deleted(self):
        return SoftDeleteQuerySet(self.model, using=self._db).all()


class SoftDeleteModel(models.Model):
    is_deleted = models.BooleanField(default=False, db_index=True)
    deleted_at = models.DateTimeField(null=True, blank=True)

    objects = SoftDeleteManager()
    all_objects = SoftDeleteQuerySet.as_manager()

    class Meta:
        abstract = True

    def delete(self, using=None, keep_parents=False, hard=False):
        if hard:
            return super().delete(using=using, keep_parents=keep_parents)
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.save(update_fields=["is_deleted", "deleted_at"])

    def hard_delete(self):
        return super().delete()


class AdditionalUserInfo(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="additional_info")
    first_name = models.CharField(max_length=128, blank=True, null=True, default=None)
    last_name = models.CharField(max_length=128, blank=True, null=True, default=None)
    email = models.EmailField(blank=True, null=True, default=None)
    avatar = models.ImageField(upload_to="avatars/", blank=True, null=True)
    syndromes = ArrayField(base_field=models.CharField(max_length=32), size=6, blank=True, default=list)
    confirmed_syndromes = ArrayField(base_field=models.CharField(max_length=32), size=6, blank=True, default=list)
    birth_date = models.DateField(blank=True, null=True)
    is_verified = models.BooleanField(default=False, db_index=True)
    ready_for_verification = models.BooleanField(default=False, db_index=True)
    email_verified = models.BooleanField(default=False, db_index=True)
    phone = models.CharField(max_length=32, blank=True, null=True)
    phone_verified = models.BooleanField(default=False, db_index=True)
    tos_accepted = models.BooleanField(default=False)
    privacy_accepted = models.BooleanField(default=False)
    data_processing_accepted = models.BooleanField(default=False)
    consents_accepted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=["user"]),
            models.Index(fields=["is_verified"]),
            models.Index(fields=["ready_for_verification"]),
            models.Index(fields=["email_verified"]),
            models.Index(fields=["phone_verified"]),
        ]

    def clean(self):
        super().clean()
        _validate_syndromes(self.syndromes)
        _validate_syndromes(self.confirmed_syndromes)
        if any(v not in (self.syndromes or []) for v in (self.confirmed_syndromes or [])):
            raise ValidationError({"confirmed_syndromes": _("Confirmed codes must be a subset of syndromes.")})

    def __str__(self):
        return f"{self.user.username}'s info"

    @property
    def followers_count(self):
        return self.followers.filter(is_active=True).count()


class PhoneVerification(models.Model):
    class Status(models.TextChoices):
        NEW = "new", "new"
        CALLING = "calling", "calling"
        VERIFIED = "verified", "verified"
        FAILED = "failed", "failed"

    user_info = models.OneToOneField(AdditionalUserInfo, on_delete=models.CASCADE, related_name="phone_verification")
    phone = models.CharField(max_length=32)
    pin_code = models.CharField(max_length=8)
    provider_session_id = models.CharField(max_length=64, blank=True, null=True)
    provider_number = models.CharField(max_length=32, blank=True, null=True)
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.NEW, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True, db_index=True)

    def __str__(self):
        return f"{self.user_info_id}:{self.phone}:{self.status}"


class MedicalExam(SoftDeleteModel):
    user_info = models.ForeignKey("AdditionalUserInfo", on_delete=models.CASCADE, related_name="medical_exams")
    exam_date = models.DateField(db_index=True)
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ["-exam_date", "-created_at"]
        indexes = [
            models.Index(fields=["user_info", "exam_date"]),
        ]

    def __str__(self):
        return f"Exam on {self.exam_date:%Y-%m-%d}"


class MedicalDocument(SoftDeleteModel):
    exam = models.ForeignKey(MedicalExam, on_delete=models.CASCADE, related_name="documents", null=True, blank=True)
    file = models.FileField(upload_to="medical_documents/", blank=True, null=True)
    external_url = models.URLField(max_length=1000, blank=True, null=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-uploaded_at"]

    def clean(self):
        super().clean()
        if not self.file and not self.external_url:
            raise ValidationError({"external_url": _("Either a file or an external link is required.")})

    def __str__(self):
        if self.file:
            return f"Document {self.file.name}"
        if self.external_url:
            return f"ExternalLink {self.external_url}"
        return "EmptyDocument"


class Notification(SoftDeleteModel):
    NOTIFICATION_TYPES = (
        ("FOLLOW", "Follow"),
        ("EXAM_COMMENT", "ExamComment"),
        ("RECOMMENDATION", "Recommendation"),
    )
    recipient = models.ForeignKey(AdditionalUserInfo, related_name="notifications", on_delete=models.CASCADE)
    sender = models.ForeignKey(AdditionalUserInfo, related_name="sent_notifications", on_delete=models.CASCADE)
    notification_type = models.CharField(max_length=50, choices=NOTIFICATION_TYPES, db_index=True)
    message = models.TextField(blank=True)
    is_read = models.BooleanField(default=False, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        indexes = [
            models.Index(fields=["recipient", "is_read", "-created_at"]),
            models.Index(fields=["sender", "-created_at"]),
        ]

    def __str__(self):
        return f"{self.notification_type} from {self.sender.user.username} -> {self.recipient.user.username}"


class Follower(models.Model):
    follower = models.ForeignKey("AdditionalUserInfo", related_name="following", on_delete=models.CASCADE)
    following = models.ForeignKey("AdditionalUserInfo", related_name="followers", on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    is_active = models.BooleanField(default=True, db_index=True)

    class Meta:
        unique_together = ("follower", "following")
        indexes = [
            models.Index(fields=["follower", "following", "is_active"]),
        ]

    def __str__(self):
        status = "active" if self.is_active else "inactive"
        return f"{status} {self.follower.user.username} -> {self.following.user.username}"


class ExamComment(SoftDeleteModel):
    exam = models.ForeignKey(MedicalExam, on_delete=models.CASCADE, related_name="comments")
    author = models.ForeignKey(AdditionalUserInfo, on_delete=models.CASCADE, related_name="exam_comments")
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ["created_at"]
        indexes = [
            models.Index(fields=["exam", "created_at"]),
        ]

    def __str__(self):
        return f"Comment by {self.author.user.username} on {self.exam.exam_date:%Y-%m-%d}"


class Recommendation(SoftDeleteModel):
    patient = models.ForeignKey(AdditionalUserInfo, on_delete=models.CASCADE, related_name="recommendations", db_index=True)
    author = models.ForeignKey(AdditionalUserInfo, on_delete=models.CASCADE, related_name="sent_recommendations", db_index=True)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["patient", "-created_at"]),
            models.Index(fields=["author", "-created_at"]),
        ]

    def __str__(self):
        return f"Recommendation to {self.patient.user.username} by {self.author.user.username}"
