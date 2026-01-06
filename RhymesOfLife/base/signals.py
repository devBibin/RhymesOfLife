from django.conf import settings
from django.contrib.auth import get_user_model
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils.translation import gettext as _
from .models import MedicalDocument
from .utils.telegram import send_message

from .models import Notification
from .utils.telegram_user import send_message_to_userinfo
from .utils.logging import get_app_logger

User = get_user_model()

log = get_app_logger(__name__)


def _admin_url(app_label: str, model: str, pk: int) -> str:
    base = getattr(settings, "BASE_URL", "").rstrip("/")
    if not base:
        return ""
    return f"{base}/admin/{app_label}/{model}/{pk}/change/"


@receiver(post_save, sender=User, dispatch_uid="notify_admin_on_user_created")
def notify_admin_on_user_created(sender, instance: User, created: bool, **kwargs):
    if not created:
        return
    admin_link = _admin_url("auth", "user", instance.pk)
    lines = [
        _("New user registered"),
        f"{_('Username')}: {instance.username}",
        f"{_('User ID')}: {instance.pk}",
        f"{_('Email')}: {instance.email or '—'}",
    ]
    if admin_link:
        lines.append(f"{_('Admin')}: {admin_link}")
    send_message("\n".join(lines))


@receiver(post_save, sender=MedicalDocument, dispatch_uid="notify_admin_on_document_created")
def notify_admin_on_document_created(sender, instance: MedicalDocument, created: bool, **kwargs):
    if not created:
        return
    exam = instance.exam
    user = getattr(getattr(exam, "user_info", None), "user", None)
    admin_link = _admin_url("base", "medicaldocument", instance.pk)
    lines = [
        _("New medical document uploaded"),
        f"{_('Document ID')}: {instance.pk}",
        f"{_('File')}: {getattr(instance.file, 'name', '—')}",
        f"{_('Exam ID')}: {getattr(exam, 'id', '—')}",
        f"{_('Exam date')}: {getattr(exam, 'exam_date', '—')}",
        f"{_('User')}: {getattr(user, 'username', '—')} (#{getattr(user, 'id', '—')})",
    ]
    if admin_link:
        lines.append(f"{_('Admin')}: {admin_link}")
    send_message("\n".join(lines))


@receiver(post_save, sender=Notification)
def notify_user_in_telegram(sender, instance: Notification, created, **kwargs):
    if not created:
        return
    try:
        if instance.recipient:
            payload = getattr(instance, "payload", None) or {}
            if isinstance(payload, dict) and payload.get("skip_telegram"):
                return
            send_message_to_userinfo(instance.message or "", instance.recipient)
    except Exception:
        log.exception("Failed to push Telegram notification: id=%s", instance.id)
