import requests
from django.conf import settings
from .logging import get_app_logger

log = get_app_logger(__name__)
_API = "https://api.telegram.org/bot{token}/{method}"


def _enabled():
    return bool(settings.TELEGRAM_BOT_TOKEN) and bool(settings.TELEGRAM_STAFF_CHAT_IDS)


def send_message(text: str, *, parse_mode: str | None = None) -> None:
    if not _enabled():
        return
    url = _API.format(token=settings.TELEGRAM_BOT_TOKEN, method="sendMessage")
    for cid in settings.TELEGRAM_STAFF_CHAT_IDS:
        payload = {"chat_id": cid, "text": text, "disable_web_page_preview": True}
        if parse_mode:
            payload["parse_mode"] = parse_mode
        try:
            r = requests.post(url, json=payload, timeout=7)
            if r.status_code != 200:
                log.warning("Telegram sendMessage failed: chat_id=%s status=%s body=%s", cid, r.status_code, r.text)
        except Exception:
            log.exception("Telegram sendMessage exception: chat_id=%s", cid)
