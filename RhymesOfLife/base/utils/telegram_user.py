from __future__ import annotations

import requests
from django.conf import settings

from .logging import get_app_logger

log = get_app_logger(__name__)
_API = "https://api.telegram.org/bot{token}/{method}"


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
    url = _API.format(token=settings.TELEGRAM_BOT_TOKEN_USERS, method="sendMessage")
    payload = {"chat_id": chat_id, "text": text, "disable_web_page_preview": True}
    try:
        r = requests.post(url, json=payload, timeout=7)
        if r.status_code != 200:
            log.warning(
                "Telegram user sendMessage failed: chat_id=%s status=%s body=%s",
                chat_id, r.status_code, r.text,
            )
    except Exception:
        log.exception("Telegram user sendMessage exception: chat_id=%s", chat_id)