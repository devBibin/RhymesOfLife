from __future__ import annotations

from django.conf import settings

from .logging import get_app_logger
from .telegram import send_bot_message

log = get_app_logger(__name__)


def _enabled() -> bool:
    return bool(getattr(settings, "TELEGRAM_BOT_TOKEN_USERS", None))


def _resolve_chat_id(userinfo) -> int | str | None:
    tg_acc = getattr(userinfo, "telegram_account", None)
    if tg_acc and getattr(tg_acc, "telegram_id", None):
        return tg_acc.telegram_id

    user = getattr(userinfo, "user", None)
    tg_acc_u = getattr(user, "telegram_account", None) if user else None
    if tg_acc_u and getattr(tg_acc_u, "telegram_id", None):
        return tg_acc_u.telegram_id

    return getattr(userinfo, "telegram_chat_id", None)


def send_message_to_userinfo(text: str, userinfo) -> None:
    if not _enabled():
        return
    chat_id = _resolve_chat_id(userinfo)
    if not chat_id:
        return
    ok = send_bot_message(
        token=settings.TELEGRAM_BOT_TOKEN_USERS,
        chat_id=chat_id,
        text=text,
        logger=log,
    )
    if not ok:
        log.warning("Telegram user sendMessage failed: chat_id=%s", chat_id)
