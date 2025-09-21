import os
import sys
import json
import time
import signal
import logging
import traceback
from pathlib import Path
from typing import Optional

import requests
import telebot

try:
    from RhymesOfLifeShadows.create_log import create_log
except ImportError:
    CURR_DIR = Path(__file__).resolve().parent
    PARENT = CURR_DIR.parent
    for p in (str(PARENT), str(CURR_DIR)):
        if p not in sys.path:
            sys.path.insert(0, p)
    from create_log import create_log

SHADOWS_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SHADOWS_DIR.parent
LOGS_DIR = SHADOWS_DIR / "logs"
LOGS_DIR.mkdir(parents=True, exist_ok=True)

log = create_log("telegram_poller.log", "TelegramPoller")

try:
    import gettext
    LOCALE_DIR = PROJECT_ROOT / "locale"
    trans = gettext.translation("django", localedir=str(LOCALE_DIR), fallback=True)
    _ = trans.gettext
except Exception:
    _ = lambda s: s

ENV_PATH = PROJECT_ROOT / "environment.json"
env = {}
try:
    with open(ENV_PATH, "r", encoding="utf-8") as f:
        env = json.load(f)
except Exception:
    log.warning(_("environment.json not found or invalid at %s"), ENV_PATH)

TOKEN = os.environ.get("TG_USER_BOT_TOKEN") or env.get("TELEGRAM_BOT_TOKEN_USERS", "")
if not TOKEN:
    log.critical(_("User bot token not found. Set TG_USER_BOT_TOKEN or environment.json[TELEGRAM_BOT_TOKEN_USERS]."))
    sys.exit(1)

BASE_URL = (
    os.environ.get("TG_BASE_URL")
    or env.get("TG_BASE_URL", "")
    or env.get("BASE_URL", "")
).strip()

FORWARD_URL_ENV = os.environ.get("TG_FORWARD_URL")


def _mask_secret(s: str, head: int = 6, tail: int = 4) -> str:
    if not s:
        return ""
    if len(s) <= head + tail:
        return s
    return f"{s[:head]}…{s[-tail:]}"


def _extract_token_from_endpoint(url: str) -> Optional[str]:
    try:
        part = url.split("/telegram/webhook/", 1)[1]
        token = part.strip("/").split("/", 1)[0]
        return token
    except Exception:
        return None


def _describe_message(msg: telebot.types.Message) -> str:
    ctype = msg.content_type
    chat_id = getattr(msg.chat, "id", "?")
    text = getattr(msg, "text", "") or ""
    if text:
        text = text.replace("\n", " ")
        if len(text) > 120:
            text = text[:117] + "..."
    has_contact = bool(getattr(msg, "contact", None))
    return f"id={msg.message_id} chat={chat_id} type={ctype} text='{text}' contact={has_contact}"


def _build_default_endpoint() -> str:
    if BASE_URL:
        base = BASE_URL.rstrip("/")
        return f"{base}/telegram/webhook/{TOKEN}/"
    if (os.environ.get("ENV", "").lower() in {"prod", "production"}) or env.get("ENV", "").lower() in {"prod", "production"}:
        return f"http://127.0.0.1/telegram/webhook/{TOKEN}/"
    return f"http://127.0.0.1:8000/telegram/webhook/{TOKEN}/"


DEFAULT_ENDPOINT = _build_default_endpoint()
ENDPOINT = FORWARD_URL_ENV or DEFAULT_ENDPOINT

session = requests.Session()


def _forward_update(update: dict) -> tuple[int, str]:
    r = session.post(
        ENDPOINT,
        data=json.dumps(update),
        headers={"Content-Type": "application/json"},
        timeout=10,
    )
    return r.status_code, r.text


bot = telebot.TeleBot(TOKEN, parse_mode=None)

try:
    bot.remove_webhook()
    log.info(_("Webhook removed (if was set)."))
except Exception:
    log.warning(_("Failed to remove webhook; continuing."), exc_info=True)

STOP = False


def shutdown_handler(signum, frame):
    global STOP
    log.info(_("Received shutdown signal (%s)"), signum)
    STOP = True
    try:
        bot.stop_polling()
    except Exception:
        pass


signal.signal(signal.SIGINT, shutdown_handler)
signal.signal(signal.SIGTERM, shutdown_handler)


@bot.message_handler(content_types=["text", "contact"])
def on_update(message: telebot.types.Message):
    desc = _describe_message(message)
    log.info(_("RX %s"), desc)
    update = {"update_id": message.message_id, "message": message.json}
    try:
        status, body = _forward_update(update)
        if status == 200:
            log.info(_("POST %s : %s"), ENDPOINT, status)
        else:
            if status == 403:
                log.error(_("POST %s : 403 Forbidden (token mismatch?)"), ENDPOINT)
            elif status == 404:
                log.error(_("POST %s : 404 Not Found (check Django URLConf/path)"), ENDPOINT)
            elif 500 <= status < 600:
                log.error(_("POST %s : %s (server error). Body: %s"), ENDPOINT, status, body[:300])
            else:
                log.warning(_("POST %s : %s. Body: %s"), ENDPOINT, status, body[:300])
    except requests.Timeout:
        log.error(_("Timeout while POSTing to %s"), ENDPOINT)
    except requests.ConnectionError as e:
        log.error(_("Connection error to %s: %s"), ENDPOINT, e)
    except Exception:
        log.exception(_("Unexpected error while forwarding update"))


if __name__ == "__main__":
    try:
        me = bot.get_me()
        ep_token = _extract_token_from_endpoint(ENDPOINT)
        token_mismatch = (ep_token is not None and ep_token != TOKEN)
        log.info(_("Starting Telegram poller"))
        log.info(_("Bot: @%s (id=%s)"), getattr(me, "username", "?"), getattr(me, "id", "?"))
        log.info(_("Endpoint: %s"), ENDPOINT)
        log.info(_("Token: %s"), _mask_secret(TOKEN))
        if token_mismatch:
            log.error(_("Endpoint token (%s) != bot token (%s). Fix TG_FORWARD_URL or TOKEN!"), _mask_secret(ep_token or ""), _mask_secret(TOKEN))
        backoff = 3
        while not STOP:
            try:
                bot.infinity_polling(skip_pending=True, timeout=30)
            except KeyboardInterrupt:
                shutdown_handler("KeyboardInterrupt", None)
            except Exception as e:
                log.critical(_("Polling crashed: %s\n%s"), e, traceback.format_exc())
                if STOP:
                    break
                log.info(_("Retrying in %ss..."), backoff)
                time.sleep(backoff)
                backoff = min(backoff * 2, 60)
            else:
                if not STOP:
                    log.warning(_("Polling stopped unexpectedly. Restarting soon..."))
                    time.sleep(2)
    finally:
        log.info(_("Poller stopped."))
