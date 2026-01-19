import random
from datetime import timedelta
from typing import Optional

from django.conf import settings
from django.core.cache import cache
from django.template.loader import render_to_string
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.contrib.auth import get_user_model

from ..models import PasswordResetCode
from .logging import get_security_logger
from .telegram_user import send_message_to_userinfo
from .email_sender import send_email

log = get_security_logger()
User = get_user_model()


def _rand_code(length: int) -> str:
    return "".join(random.choices("0123456789", k=length))


def _rate_key(prefix: str, value: str) -> str:
    return f"pwdreset:{prefix}:{value}"


def _rate_allow(prefix: str, value: str, max_calls: int, window_sec: int) -> bool:
    k = _rate_key(prefix, value)
    cur = cache.get(k)
    if cur is None:
        cache.set(k, 1, window_sec)
        return True
    if int(cur) >= max_calls:
        return False
    try:
        cache.incr(k)
    except Exception:
        cache.set(k, int(cur) + 1, window_sec)
    return True


def create_reset_code(user: User, channel: str, ip: Optional[str] = None, ua: Optional[str] = None) -> PasswordResetCode:
    ttl = int(getattr(settings, "PASSWORD_RESET_CODE_TTL_MIN", 15))
    length = int(getattr(settings, "PASSWORD_RESET_CODE_LENGTH", 6))
    now = timezone.now()
    PasswordResetCode.objects.filter(user=user, used_at__isnull=True, expires_at__gt=now).delete()
    rec = PasswordResetCode.objects.create(
        user=user,
        channel=channel,
        code=_rand_code(length),
        expires_at=now + timedelta(minutes=ttl),
        attempts_left=int(getattr(settings, "PASSWORD_RESET_MAX_ATTEMPTS", 5)),
        ip=ip or "",
        ua=(ua or "")[:256],
    )
    return rec


def send_code_email(user: User, code: str) -> None:
    if not getattr(user, "email", None):
        log.warning("email.password_reset.skip user_id=%s reason=no_email", user.id)
        return

    ttl = int(getattr(settings, "PASSWORD_RESET_CODE_TTL_MIN", 15))
    subject = _("Password reset code")
    text = _("Your password reset code is %(code)s. It expires in %(minutes)s minutes.") % {
        "code": code,
        "minutes": ttl,
    }
    html = render_to_string("emails/password_reset_code.html", {"code": code, "ttl": ttl, "user": user})

    log.info("email.password_reset.prepare user_id=%s email=%s", user.id, user.email)
    ok = send_email(
        {
            "to": user.email,
            "subject": subject,
            "text": text,
            "html": html,
        },
        logger=log,
    )
    if not ok:
        log.warning("email.password_reset.failed user_id=%s email=%s", user.id, user.email)


def send_code_telegram(user: User, code: str) -> None:
    info = getattr(user, "additional_info", None)
    if not info:
        return
    ttl = int(getattr(settings, "PASSWORD_RESET_CODE_TTL_MIN", 15))
    text = _("Your password reset code is %(code)s. It expires in %(minutes)s minutes.") % {
        "code": code,
        "minutes": ttl,
    }
    send_message_to_userinfo(text, info)


def user_can_receive_telegram(user: User) -> bool:
    info = getattr(user, "additional_info", None)
    acc = getattr(info, "telegram_account", None) if info else None
    return bool(acc and acc.telegram_verified and acc.telegram_id)


def resolve_user_by_identifier(identifier: str) -> Optional[User]:
    q = (identifier or "").strip().lower()
    if not q:
        return None
    try:
        return User.objects.get(username__iexact=q)
    except User.DoesNotExist:
        pass
    try:
        return User.objects.get(email__iexact=q)
    except User.DoesNotExist:
        return None
