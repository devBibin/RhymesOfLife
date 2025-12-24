from django.db import models
from django.utils import timezone
from django.db.utils import ProgrammingError, OperationalError
from django.contrib.auth import get_user_model
from django.contrib.postgres.fields import ArrayField
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from django.utils.translation import gettext as _g
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator, MaxLengthValidator
from django.db.models import Q, UniqueConstraint

import uuid


User = get_user_model()


def _safe_username(aui):
    try:
        if not aui:
            return _g("unknown")
        u = getattr(aui, "user", None)
        name = getattr(u, "username", None)
        return name or _g("unknown")
    except Exception:
        return _g("unknown")


class PasswordResetCode(models.Model):
    class Channel(models.TextChoices):
        EMAIL = "email", "email"
        TELEGRAM = "telegram", "telegram"

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="password_reset_codes", db_index=True)
    channel = models.CharField(max_length=16, choices=Channel.choices, db_index=True)
    code = models.CharField(max_length=16, db_index=True)
    token = models.UUIDField(default=uuid.uuid4, editable=False, db_index=True)
    expires_at = models.DateTimeField(db_index=True)
    attempts_left = models.PositiveSmallIntegerField(default=5)
    used_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    ip = models.GenericIPAddressField(null=True, blank=True)
    ua = models.CharField(max_length=256, null=True, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=["user", "channel", "expires_at"]),
            models.Index(fields=["token", "code"]),
        ]

    def is_active(self):
        return self.used_at is None and self.expires_at > timezone.now() and self.attempts_left > 0


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
        try:
            rec = cls.objects.filter(key=key).values_list("value", flat=True).first()
        except (ProgrammingError, OperationalError):
            return default
        if isinstance(rec, list):
            return rec
        return default


_DEFAULT_SYNDROME_CHOICES = [
    ["ndct", _("Undifferentiated connective tissue dysplasia")],
    ["ehlers_danlos", _("Ehlers–Danlos syndrome")],
    ["marfan", _("Marfan syndrome")],
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
    language = models.CharField(max_length=10, choices=settings.LANGUAGES, default="ru")
    first_name = models.CharField(max_length=128, blank=True, null=True, default=None)
    last_name = models.CharField(max_length=128, blank=True, null=True, default=None)
    email = models.EmailField(blank=True, null=True, default=None)
    avatar = models.ImageField(upload_to="avatars/", blank=True, null=True)
    syndromes = ArrayField(base_field=models.CharField(max_length=32), size=6, blank=True, default=list)
    confirmed_syndromes = ArrayField(base_field=models.CharField(max_length=32), size=6, blank=True, default=list)
    birth_date = models.DateField(blank=True, null=True)
    about_me = models.TextField(blank=True, validators=[MaxLengthValidator(250)])
    is_verified = models.BooleanField(default=False, db_index=True)
    ready_for_verification = models.BooleanField(default=False, db_index=True)
    email_verified = models.BooleanField(default=False, db_index=True)
    phone = models.CharField(max_length=32, blank=True, null=True)
    phone_verified = models.BooleanField(default=False, db_index=True)
    tos_accepted = models.BooleanField(default=False)
    privacy_accepted = models.BooleanField(default=False)
    data_processing_accepted = models.BooleanField(default=False)
    consents_accepted_at = models.DateTimeField(null=True, blank=True)
    censorship_enabled = models.BooleanField(default=False, db_index=True, verbose_name=_("Pre-moderation enabled"))
    is_banned = models.BooleanField(default=False, db_index=True, verbose_name=_("Banned"))
    banned_reason = models.CharField(max_length=255, blank=True, default="", verbose_name=_("Ban reason"))
    banned_at = models.DateTimeField(null=True, blank=True, verbose_name=_("Banned at"))
    banned_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="banned_users",
        verbose_name=_("Banned by")
    )

    class Meta:
        indexes = [
            models.Index(fields=["user"]),
            models.Index(fields=["is_verified"]),
            models.Index(fields=["ready_for_verification"]),
            models.Index(fields=["email_verified"]),
            models.Index(fields=["phone_verified"]),
            models.Index(fields=["is_banned"]),
        ]
        permissions = [
            ("view_patient_list", _("Can view patient list")),
        ]

    def clean(self):
        super().clean()
        _validate_syndromes(self.syndromes)
        _validate_syndromes(self.confirmed_syndromes)
        if any(v not in (self.syndromes or []) for v in (self.confirmed_syndromes or [])):
            raise ValidationError({"confirmed_syndromes": _("Confirmed codes must be a subset of syndromes.")})

    def __str__(self):
        return f"{_safe_username(self)}'s info"

    @property
    def followers_count(self):
        return self.followers.filter(is_active=True).count()

    def ban(self, by=None, reason=""):
        from django.utils import timezone
        self.is_banned = True
        self.banned_at = timezone.now()
        self.banned_by = by
        self.banned_reason = reason or ""
        self.save(update_fields=["is_banned", "banned_at", "banned_by", "banned_reason"])

    def unban(self):
        self.is_banned = False
        self.banned_at = None
        self.banned_by = None
        self.banned_reason = ""
        self.save(update_fields=["is_banned", "banned_at", "banned_by", "banned_reason"])


class TelegramAccount(models.Model):
    user_info = models.OneToOneField("AdditionalUserInfo", on_delete=models.CASCADE, related_name="telegram_account")
    telegram_id = models.CharField(max_length=50, unique=True, null=True, blank=True)
    username = models.CharField(max_length=100, null=True, blank=True)
    first_name = models.CharField(max_length=100, null=True, blank=True)
    last_name = models.CharField(max_length=100, null=True, blank=True)
    language_code = models.CharField(max_length=10, null=True, blank=True)
    activation_token = models.UUIDField(default=uuid.uuid4, unique=True, null=True, blank=True)
    telegram_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=["telegram_id"]),
            models.Index(fields=["activation_token"]),
            models.Index(fields=["telegram_verified"]),
        ]

    def __str__(self):
        owner = _safe_username(getattr(self, "user_info", None))
        return f"tg:{self.telegram_id or '-'} for {owner}"


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
        permissions = [
            ("view_patient_exams", _("Can view patient exams")),
            ("modify_patient_exams", _("Can create and edit patient exams")),
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
    class Source(models.TextChoices):
        USER = "user", "User"
        ADMIN = "admin", "Admin"
        SYSTEM = "system", "System"

    class Scope(models.TextChoices):
        PERSONAL = "personal", "Personal"
        BROADCAST = "broadcast", "Broadcast"

    NOTIFICATION_TYPES = (
        ("FOLLOW", "Follow"),
        ("EXAM_COMMENT", "ExamComment"),
        ("RECOMMENDATION", "Recommendation"),
        ("ADMIN_MESSAGE", "AdminMessage"),
        ("SYSTEM_MESSAGE", "SystemMessage"),
    )

    recipient = models.ForeignKey(AdditionalUserInfo, related_name="notifications", on_delete=models.CASCADE)
    sender = models.ForeignKey(
        AdditionalUserInfo, related_name="sent_notifications", on_delete=models.SET_NULL, null=True, blank=True
    )
    notification_type = models.CharField(max_length=50, choices=NOTIFICATION_TYPES, db_index=True)
    title = models.CharField(max_length=140, blank=True)
    message = models.TextField(blank=True)
    url = models.URLField(max_length=500, blank=True)
    payload = models.JSONField(default=dict, blank=True)
    source = models.CharField(max_length=16, choices=Source.choices, default=Source.USER, db_index=True)
    scope = models.CharField(max_length=16, choices=Scope.choices, default=Scope.PERSONAL, db_index=True)
    is_read = models.BooleanField(default=False, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        indexes = [
            models.Index(fields=["recipient", "is_read", "-created_at"]),
            models.Index(fields=["sender", "-created_at"]),
            models.Index(fields=["source", "scope", "-created_at"]),
            models.Index(fields=["notification_type", "-created_at"]),
        ]
        permissions = [
            ("send_notifications", _("Can send notifications")),
        ]

    def __str__(self):
        s = _safe_username(self.sender) if self.sender_id else _g("system")
        r = _safe_username(self.recipient)
        return f"{self.notification_type} [{self.source}/{self.scope}] {s} -> {r}"


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
        status = _g("active") if self.is_active else _g("inactive")
        f = _safe_username(self.follower)
        t = _safe_username(self.following)
        return f"{status} {f} -> {t}"


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
        permissions = [
            ("comment_exams", _("Can comment exams")),
            ("moderate_exam_comments", _("Can moderate exam comments")),
        ]

    def __str__(self):
        author = _safe_username(self.author)
        date_str = self.exam.exam_date.strftime("%Y-%m-%d") if getattr(self, "exam", None) else "n/a"
        return f"Comment by {author} on {date_str}"


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
        permissions = [
            ("view_recommendations", _("Can view recommendations")),
            ("write_recommendations", _("Can write recommendations")),
        ]

    def __str__(self):
        p = _safe_username(self.patient)
        a = _safe_username(self.author)
        return f"Recommendation to {p} by {a}"


def post_upload_to(instance, filename):
    return f"posts/{instance.post_id}/{filename}"


class Post(models.Model):
    author = models.ForeignKey(
        AdditionalUserInfo,
        on_delete=models.CASCADE,
        related_name="posts",
        verbose_name=_("Author"),
    )
    text = models.TextField(_("Text"), blank=True)
    is_hidden = models.BooleanField(_("Hidden by author"), default=False, db_index=True)
    is_deleted = models.BooleanField(_("Soft-deleted"), default=False, db_index=True)

    is_approved = models.BooleanField(_("Approved by admin"), default=False, db_index=True)
    approved_at = models.DateTimeField(_("Approved at"), null=True, blank=True)
    approved_by = models.ForeignKey(
        User, null=True, blank=True, on_delete=models.SET_NULL, related_name="approved_posts", verbose_name=_("Approved by")
    )

    likes_count = models.PositiveIntegerField(_("Likes count"), default=0)
    comments_count = models.PositiveIntegerField(_("Comments count"), default=0)

    created_at = models.DateTimeField(_("Created at"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Updated at"), auto_now=True)

    is_hidden_by_reports = models.BooleanField(_("Hidden by reports"), default=False, db_index=True)
    reports_count = models.PositiveIntegerField(_("Reports count"), default=0)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = _("Post")
        verbose_name_plural = _("Posts")

    def __str__(self):
        return f"Post#{self.pk} by {_safe_username(self.author)}"

    @property
    def visible_comments(self):
        return self.comments.filter(is_deleted=False)


class PostReport(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="reports", db_index=True)
    author = models.ForeignKey(AdditionalUserInfo, on_delete=models.CASCADE, related_name="post_reports", db_index=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        unique_together = ("post", "author")
        indexes = [models.Index(fields=["post", "author"])]

    def __str__(self):
        return f"🚩 {_safe_username(self.author)} → {self.post_id}"


class PostImage(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="images", verbose_name=_("Post"))
    image = models.ImageField(upload_to=post_upload_to, verbose_name=_("Image"))
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _("Post image")
        verbose_name_plural = _("Post images")


class PostLike(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="likes")
    author = models.ForeignKey(AdditionalUserInfo, on_delete=models.CASCADE)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("post", "author")
        verbose_name = _("Post like")
        verbose_name_plural = _("Post likes")

    def __str__(self):
        return f"👍 {_safe_username(self.author)} → {self.post_id}"


class PostComment(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="comments")
    author = models.ForeignKey(AdditionalUserInfo, on_delete=models.CASCADE)
    text = models.TextField(_("Text"))
    created_at = models.DateTimeField(_("Created at"), auto_now_add=True)
    edited_at = models.DateTimeField(_("Edited at"), null=True, blank=True)
    is_deleted = models.BooleanField(_("Soft-deleted"), default=False)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = _("Post comment")
        verbose_name_plural = _("Post comments")

    def __str__(self):
        return _g("🗑 Deleted comment") if self.is_deleted else f"💬 {_safe_username(self.author)}: {self.text[:30]}"


class HelpRequest(models.Model):
    name = models.CharField(_('name'), max_length=200, blank=True)
    email = models.EmailField(_('email'), blank=True)
    telegram = models.CharField(_('telegram'), max_length=100, blank=True)
    message = models.TextField(_('message'))
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)

    is_processed = models.BooleanField(_('processed'), default=False, db_index=True)
    processed_at = models.DateTimeField(_('processed at'), null=True, blank=True)
    processed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name='processed_help_requests'
    )

    class Meta:
        verbose_name = _('help request')
        verbose_name_plural = _('help requests')
        ordering = ['-created_at']
        permissions = [
            ("view_help_requests", _("Can view help requests")),
            ("process_help_requests", _("Can process help requests")),
        ]

    def __str__(self):
        return f"{self.name or self.email or self.pk} - {self.created_at:%Y-%m-%d}"

    def mark_processed(self, user):
        self.is_processed = True
        self.processed_at = timezone.now()
        self.processed_by = user
        self.save(update_fields=['is_processed', 'processed_at', 'processed_by'])

    def mark_unprocessed(self):
        self.is_processed = False
        self.processed_at = None
        self.processed_by = None
        self.save(update_fields=['is_processed', 'processed_at', 'processed_by'])


class WellnessSettings(models.Model):
    class ReminderInterval(models.IntegerChoices):
        NEVER = 0, _("Never")
        DAILY = 1, _("Every day")
        EVERY_3_DAYS = 3, _("Every 3 days")
        EVERY_7_DAYS = 7, _("Every 7 days")

    user_info = models.OneToOneField("AdditionalUserInfo", on_delete=models.CASCADE, related_name="wellness_settings")
    tg_notifications_enabled = models.BooleanField(default=True, db_index=True)
    email_notifications_enabled = models.BooleanField(default=True, db_index=True)
    reminder_hour = models.PositiveSmallIntegerField(default=20, validators=[MinValueValidator(0), MaxValueValidator(23)])
    reminder_minute = models.PositiveSmallIntegerField(default=0, validators=[MinValueValidator(0), MaxValueValidator(59)])
    reminder_tz = models.CharField(max_length=64, blank=True, default="")
    reminder_interval = models.PositiveSmallIntegerField(
        choices=ReminderInterval.choices,
        default=ReminderInterval.EVERY_3_DAYS,
        db_index=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=["tg_notifications_enabled"]),
            models.Index(fields=["email_notifications_enabled"]),
            models.Index(fields=["reminder_interval"]),
        ]

    def __str__(self):
        return f"WellnessSettings for {_safe_username(self.user_info)}"


class WellnessEntry(SoftDeleteModel):
    user_info = models.ForeignKey("AdditionalUserInfo", on_delete=models.CASCADE, related_name="wellness_entries", db_index=True)
    date = models.DateField(db_index=True)
    score = models.PositiveSmallIntegerField(validators=[MinValueValidator(1), MaxValueValidator(10)])
    note = models.TextField(blank=True, validators=[MaxLengthValidator(1000)])
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ["-date", "-created_at"]
        indexes = [
            models.Index(fields=["user_info", "date"]),
            models.Index(fields=["user_info", "-created_at"]),
        ]
        constraints = [
            UniqueConstraint(
                fields=["user_info", "date"],
                condition=Q(is_deleted=False),
                name="uniq_wellness_user_date_alive",
            )
        ]
