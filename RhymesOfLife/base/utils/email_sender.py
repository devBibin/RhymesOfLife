from __future__ import annotations

import logging
import sys
from pathlib import Path
from typing import Any

from django.conf import settings

log = logging.getLogger(__name__)


def _ensure_project_root_on_path() -> None:
    root = Path(__file__).resolve().parents[3]
    root_str = str(root)
    if root_str not in sys.path:
        sys.path.insert(0, root_str)


def _get_provider(explicit: str | None = None) -> str:
    if explicit:
        return explicit
    return str(getattr(settings, "EMAIL_PROVIDER", "") or "postbox_api").strip().lower()


def _normalize_payload(payload: dict[str, Any]) -> dict[str, Any]:
    p = dict(payload or {})

    if "to" not in p:
        p["to"] = p.get("email")

    if "text" not in p and "body" in p:
        p["text"] = p.get("body")

    if "from_email" not in p:
        p["from_email"] = p.get("from") or p.get("fromEmail")

    return p


def _coerce_str(v: Any) -> str:
    if v is None:
        return ""
    return str(v)


def _coerce_types(p: dict[str, Any]) -> dict[str, Any]:
    p = dict(p)
    if "subject" in p:
        p["subject"] = _coerce_str(p.get("subject"))
    if "text" in p:
        p["text"] = _coerce_str(p.get("text"))
    if "html" in p and p.get("html") is not None:
        p["html"] = _coerce_str(p.get("html"))
    if "to" in p and p.get("to") is not None:
        p["to"] = _coerce_str(p.get("to")).strip()
    if "from_email" in p and p.get("from_email") is not None:
        p["from_email"] = _coerce_str(p.get("from_email")).strip()
    return p


def _validate_payload(p: dict[str, Any]) -> None:
    to_addr = (p.get("to") or "").strip()
    subject = (p.get("subject") or "").strip()
    text = (p.get("text") or "").strip() if p.get("text") is not None else ""
    html = (p.get("html") or "").strip() if p.get("html") is not None else ""

    if not to_addr:
        raise ValueError("Email payload missing 'to'")
    if not subject:
        raise ValueError("Email payload missing 'subject'")
    if not text and not html:
        raise ValueError("Email payload missing 'text' or 'html'")


def send_email(payload: dict[str, Any], *, logger: logging.Logger | None = None, provider: str | None = None) -> bool:
    logger = logger or log
    _ensure_project_root_on_path()

    from RhymesOfLifeShadows.EmailVerificationSender import EmailVerificationSender  # noqa: E402

    prov = _get_provider(provider)
    p = _coerce_types(_normalize_payload(payload))
    if prov == "postbox_api" and not p.get("from_email"):
        p["from_email"] = getattr(settings, "POSTBOX_FROM_EMAIL", None)
    _validate_payload(p)

    to_addr = p["to"]
    subject = p["subject"]
    from_email = p.get("from_email") or ""

    logger.info(
        "email.send.prepare provider=%s to=%s subject=%s from=%s",
        prov,
        to_addr,
        subject[:160],
        from_email or "-",
    )

    try:
        sender = EmailVerificationSender(provider=prov, logger=logger)
        ok = bool(sender.send_email(p))
        if ok:
            logger.info("email.send.ok provider=%s to=%s", prov, to_addr)
        else:
            logger.warning("email.send.failed provider=%s to=%s reason=unknown", prov, to_addr)
        return ok
    except Exception as exc:
        logger.exception("email.send.error provider=%s to=%s error=%s", prov, to_addr, exc)
        return False
