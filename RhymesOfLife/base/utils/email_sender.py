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


def _validate_payload(p: dict[str, Any]) -> None:
    to_addr = (p.get("to") or "").strip()
    subject = p.get("subject")
    text = p.get("text")
    html = p.get("html")

    if not to_addr:
        raise ValueError("Email payload missing 'to'")
    if subject is None or str(subject).strip() == "":
        raise ValueError("Email payload missing 'subject'")
    if (text is None or str(text).strip() == "") and (html is None or str(html).strip() == ""):
        raise ValueError("Email payload missing 'text' or 'html'")


def send_email(payload: dict[str, Any], *, logger: logging.Logger | None = None, provider: str | None = None) -> bool:
    logger = logger or log
    _ensure_project_root_on_path()

    from RhymesOfLifeShadows.EmailVerificationSender import EmailVerificationSender  # noqa: E402

    prov = _get_provider(provider)
    p = _normalize_payload(payload)
    _validate_payload(p)

    to_addr = (p.get("to") or "").strip()
    subject = str(p.get("subject") or "").strip()
    from_email = (p.get("from_email") or "").strip()

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
