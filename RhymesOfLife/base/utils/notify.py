import logging
import requests
from django.conf import settings
from django.utils.translation import gettext as _
from django.utils.translation import override
from base.models import Notification, AdditionalUserInfo
from .email_sender import send_email

log = logging.getLogger(__name__)


def _send_telegram(chat_id: int | str, text: str, *, button_text: str | None = None, button_url: str | None = None) -> bool:
    token = getattr(settings, "TELEGRAM_BOT_TOKEN_USERS", "")
    if not token:
        log.error("Telegram token missing")
        return False
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": False,
    }
    if button_url:
        payload["reply_markup"] = {
            "inline_keyboard": [[{"text": button_text or _("Details"), "url": button_url}]]
        }
    try:
        r = requests.post(url, json=payload, timeout=10)
        if r.ok:
            return True
        log.warning("Telegram send failed: status=%s body=%s", r.status_code, r.text[:500])
        return False
    except requests.RequestException as e:
        log.error("Telegram request error: %s", e)
        return False


def _send_email_localized(info: AdditionalUserInfo, subject: str, body: str) -> bool:
    email = info.email or getattr(info.user, "email", None)
    if not email:
        return False
    from_email = getattr(settings, "DEFAULT_FROM_EMAIL", "no-reply@example.com")
    try:
        log.info("email.notify.prepare user_info_id=%s to=%s subject=%s", info.id, email, subject)
        with override(info.language or "en"):
            s = str(subject)
            b = str(body)
        return bool(send_email({
            "to": email,
            "subject": s,
            "text": b,
            "from_email": from_email,
        }))
    except Exception as exc:
        log.error("email.notify.failed user_info_id=%s to=%s error=%s", info.id, email, exc)
        return False


def send_notification_multichannel(
    *,
    recipient: AdditionalUserInfo,
    sender: AdditionalUserInfo | None,
    notification_type: str,
    title: str = "",
    message: str,
    url: str = "",
    button_text: str | None = None,
    payload: dict | None = None,
    source: str = Notification.Source.SYSTEM,
    scope: str = Notification.Scope.PERSONAL,
    via_site: bool = True,
    via_telegram: bool = True,
    via_email: bool = True,
    email_subject: str | None = None,
    email_body: str | None = None,
) -> dict:
    created = None
    payload = dict(payload or {})
    if via_site:
        payload["skip_telegram"] = True
        created = Notification.objects.create(
            recipient=recipient,
            sender=sender,
            notification_type=notification_type,
            title=title,
            message=message,
            url=url,
            payload=payload,
            source=source,
            scope=scope,
        )

    tg_sent = False
    if via_telegram:
        tg = getattr(recipient, "telegram_account", None)
        if tg and getattr(tg, "telegram_verified", False) and getattr(tg, "telegram_id", None):
            tg_text = f"<b>{title}</b>\n{message}" if title else message
            tg_sent = _send_telegram(tg.telegram_id, tg_text, button_text=button_text, button_url=url or None)

    mail_sent = False
    if via_email:
        subj = email_subject if email_subject is not None else title or _("Notification")
        body = email_body if email_body is not None else (f"{message}\n{url}" if url else message)
        mail_sent = _send_email_localized(recipient, subj, body)

    return {
        "notification_id": getattr(created, "id", None),
        "telegram_sent": tg_sent,
        "email_sent": mail_sent,
    }
