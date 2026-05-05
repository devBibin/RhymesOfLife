from __future__ import annotations

from typing import Any
from urllib.parse import urlsplit, urlunsplit

import requests
from django.conf import settings
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from .logging import get_app_logger

log = get_app_logger(__name__)

_API = "https://api.telegram.org/bot{token}/{method}"
_TIMEOUT = 20
_MAX_RETRIES = 3
_RETRYABLE_STATUSES = (429, 500, 502, 503, 504)

_session: requests.Session | None = None


def _build_session() -> requests.Session:
    retry = Retry(
        total=_MAX_RETRIES,
        connect=_MAX_RETRIES,
        read=_MAX_RETRIES,
        status=_MAX_RETRIES,
        backoff_factor=1,
        status_forcelist=_RETRYABLE_STATUSES,
        allowed_methods=frozenset({"GET", "POST"}),
        raise_on_status=False,
    )
    adapter = HTTPAdapter(max_retries=retry)
    session = requests.Session()
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session


def _get_session() -> requests.Session:
    global _session
    if _session is None:
        _session = _build_session()
    return _session


def _mask_proxy_url(proxy_url: str | None) -> str:
    if not proxy_url:
        return "direct"
    parts = urlsplit(proxy_url)
    hostname = parts.hostname or ""
    port = f":{parts.port}" if parts.port else ""
    if parts.username:
        auth = f"{parts.username}:***@"
    else:
        auth = ""
    return urlunsplit((parts.scheme, f"{auth}{hostname}{port}", parts.path, parts.query, parts.fragment))


def _get_proxies() -> dict[str, str] | None:
    proxy_url = (getattr(settings, "TELEGRAM_PROXY_URL", "") or "").strip()
    if not proxy_url:
        return None
    return {
        "http": proxy_url,
        "https": proxy_url,
    }


def _request(
    *,
    token: str,
    method: str,
    payload: dict[str, Any] | None = None,
    http_method: str = "post",
    timeout: int = _TIMEOUT,
    logger=None,
) -> requests.Response | None:
    logger = logger or log
    proxies = _get_proxies()
    proxy_label = _mask_proxy_url((proxies or {}).get("https"))
    url = _API.format(token=token, method=method)
    logger.info(
        "telegram.api.request method=%s http_method=%s timeout=%s retries=%s proxy=%s",
        method,
        http_method.upper(),
        timeout,
        _MAX_RETRIES,
        proxy_label,
    )
    try:
        response = _get_session().request(
            method=http_method.upper(),
            url=url,
            json=payload,
            timeout=timeout,
            proxies=proxies,
        )
    except requests.RequestException:
        logger.exception(
            "telegram.api.exception method=%s proxy=%s payload_keys=%s",
            method,
            proxy_label,
            sorted((payload or {}).keys()),
        )
        return None

    if response.status_code != 200:
        logger.warning(
            "telegram.api.bad_status method=%s status=%s proxy=%s body=%s",
            method,
            response.status_code,
            proxy_label,
            response.text,
        )
    return response


def telegram_api_post(token: str, method: str, payload: dict[str, Any], *, logger=None) -> requests.Response | None:
    return _request(token=token, method=method, payload=payload, http_method="post", logger=logger)


def telegram_api_get(token: str, method: str, *, logger=None) -> requests.Response | None:
    return _request(token=token, method=method, payload=None, http_method="get", logger=logger)


def send_bot_message(
    *,
    token: str,
    chat_id: int | str,
    text: str,
    parse_mode: str | None = None,
    disable_web_page_preview: bool = True,
    reply_markup: dict[str, Any] | None = None,
    logger=None,
) -> bool:
    payload: dict[str, Any] = {
        "chat_id": chat_id,
        "text": text,
        "disable_web_page_preview": disable_web_page_preview,
    }
    if parse_mode:
        payload["parse_mode"] = parse_mode
    if reply_markup:
        payload["reply_markup"] = reply_markup

    response = telegram_api_post(token, "sendMessage", payload, logger=logger)
    return bool(response and response.status_code == 200)


def get_bot_username(token: str, *, logger=None) -> str | None:
    response = telegram_api_get(token, "getMe", logger=logger)
    if not response or response.status_code != 200:
        return None
    try:
        data = response.json() or {}
    except ValueError:
        (logger or log).warning("telegram.api.invalid_json method=getMe body=%s", response.text)
        return None
    result = data.get("result") if isinstance(data, dict) else None
    username = (result or {}).get("username") if isinstance(result, dict) else None
    return username or None


def _enabled() -> bool:
    return bool(settings.TELEGRAM_BOT_TOKEN_ADMIN) and bool(settings.TELEGRAM_STAFF_CHAT_IDS)


def send_message(text: str, *, parse_mode: str | None = None) -> None:
    if not _enabled():
        return
    for cid in settings.TELEGRAM_STAFF_CHAT_IDS:
        ok = send_bot_message(
            token=settings.TELEGRAM_BOT_TOKEN_ADMIN,
            chat_id=cid,
            text=text,
            parse_mode=parse_mode,
            logger=log,
        )
        if not ok:
            log.warning("Telegram sendMessage failed: chat_id=%s", cid)
