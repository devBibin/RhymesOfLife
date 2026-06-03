import logging
from email.utils import formataddr, parseaddr

from django.conf import settings
from django.template.loader import render_to_string
from django.utils.translation import gettext as _
from django.utils.translation import override
from base.models import Notification, AdditionalUserInfo
from .email_sender import send_email
from .telegram import send_bot_message

log = logging.getLogger(__name__)


def _brand_from_email() -> str | None:
    raw_from = (
        getattr(settings, "POSTBOX_FROM_EMAIL", None)
        or getattr(settings, "DEFAULT_FROM_EMAIL", None)
        or getattr(settings, "EMAIL_HOST_USER", None)
    )
    if not raw_from:
        return None

    _, email_address = parseaddr(str(raw_from))
    if not email_address:
        email_address = str(raw_from).strip()
    return formataddr(("Ритмы жизни", email_address))


def _send_telegram(chat_id: int | str, text: str, *, button_text: str | None = None, button_url: str | None = None) -> bool:
    token = getattr(settings, "TELEGRAM_BOT_TOKEN_USERS", "")
    if not token:
        log.error("telegram.send.error reason=token_missing")
        return False
    reply_markup = None
    if button_url:
        reply_markup = {"inline_keyboard": [[{"text": button_text or _("Details"), "url": button_url}]]}
    return send_bot_message(
        token=token,
        chat_id=chat_id,
        text=text,
        parse_mode="HTML",
        disable_web_page_preview=False,
        reply_markup=reply_markup,
        logger=log,
    )


def _send_email_localized(
    info: AdditionalUserInfo,
    subject: str,
    body: str,
    *,
    html: str | None = None,
    from_email: str | None = None,
) -> bool:
    email = (info.email or getattr(info.user, "email", None) or "").strip()
    if not email:
        log.warning("email.notify.skip user_info_id=%s reason=no_email", info.id)
        return False

    try:
        with override(info.language or "en"):
            s = str(subject)
            b = str(body)

        log.info("email.notify.prepare user_info_id=%s to=%s subject=%s", info.id, email, s[:160])
        ok = bool(
            send_email(
                {
                    "to": email,
                    "subject": s,
                    "text": b,
                    "html": html,
                    "from_email": from_email or _brand_from_email(),
                },
                logger=log,
            )
        )
        if not ok:
            log.warning("email.notify.failed user_info_id=%s to=%s", info.id, email)
        return ok
    except Exception as exc:
        log.exception("email.notify.error user_info_id=%s to=%s error=%s", info.id, email, exc)
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
    email_html: str | None = None,
    email_from: str | None = None,
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
        subj = email_subject if email_subject is not None else (title or _("Notification"))
        body = email_body if email_body is not None else (f"{message}\n{url}" if url else message)
        mail_sent = _send_email_localized(recipient, subj, body, html=email_html, from_email=email_from)

    return {
        "notification_id": getattr(created, "id", None),
        "telegram_sent": tg_sent,
        "email_sent": mail_sent,
    }
