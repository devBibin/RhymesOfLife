from __future__ import annotations

import json
import uuid
from dataclasses import dataclass

import requests
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core.cache import cache
from django.db import transaction
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import render, redirect
from django.urls import reverse
from django.utils.crypto import constant_time_compare
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from ..models import AdditionalUserInfo, TelegramAccount

API = "https://api.telegram.org/bot{token}/{method}"


def _api_send(method: str, payload: dict) -> None:
    token = getattr(settings, "TELEGRAM_BOT_TOKEN_USERS", "")
    if not token:
        return
    try:
        r = requests.post(API.format(token=token, method=method), json=payload, timeout=7)
        if r.status_code != 200:
            pass
    except Exception:
        pass


def _send_text(chat_id: int, text: str) -> None:
    _api_send("sendMessage", {"chat_id": chat_id, "text": text, "disable_web_page_preview": True})


def _send_contact_request(chat_id: int, text: str) -> None:
    keyboard = {
        "keyboard": [[{"text": "Share phone", "request_contact": True}]],
        "resize_keyboard": True,
        "one_time_keyboard": True,
    }
    _api_send(
        "sendMessage",
        {"chat_id": chat_id, "text": text, "disable_web_page_preview": True, "reply_markup": keyboard},
    )


def _get_bot_username() -> str | None:

    name = getattr(settings, "TELEGRAM_BOT_USERNAME", "") or cache.get("tg_bot_username")
    if name:
        return name

    token = getattr(settings, "TELEGRAM_BOT_TOKEN_USERS", "")
    if not token:
        return None
    try:
        r = requests.get(API.format(token=token, method="getMe"), timeout=7)
        if r.status_code == 200:
            data = r.json() or {}
            name = ((data.get("result") or {}).get("username") or "") if isinstance(data, dict) else ""
            if name:
                cache.set("tg_bot_username", name, 24 * 60 * 60)
                return name
    except Exception:
        pass
    return None


@dataclass
class UpdateCtx:
    chat_id: int | None
    text: str | None
    start_payload: str | None
    phone: str | None
    tg_username: str | None
    first_name: str | None
    last_name: str | None
    lang: str | None


def _parse_update(raw: dict) -> UpdateCtx:
    msg = raw.get("message") or {}
    chat = msg.get("chat") or {}
    frm = msg.get("from") or {}
    text = msg.get("text")
    payload = None
    if isinstance(text, str) and text.startswith("/start") and len(text.split()) > 1:
        payload = text.split(" ", 1)[1].strip()

    contact = msg.get("contact") or {}
    phone = contact.get("phone_number")

    return UpdateCtx(
        chat_id=chat.get("id"),
        text=text,
        start_payload=payload,
        phone=phone,
        tg_username=frm.get("username"),
        first_name=frm.get("first_name"),
        last_name=frm.get("last_name"),
        lang=frm.get("language_code"),
    )


def _norm_phone(phone: str) -> str:
    p = (phone or "").strip()
    return p if p.startswith("+") else f"+{p}" if p else p


@login_required
@require_http_methods(["GET", "POST"])
def connect_telegram_view(request: HttpRequest) -> HttpResponse:

    user_info = request.user.additional_info
    acc, _ = TelegramAccount.objects.get_or_create(user_info=user_info)

    bot_username = _get_bot_username()
    telegram_bot_link = f"https://t.me/{bot_username}?start=activate_{acc.activation_token}" if bot_username else None
    skip_url = reverse("phone_enter")

    if request.method == "POST":
        acc.refresh_from_db()
        if acc.telegram_verified and user_info.phone_verified:
            return redirect("consents")
        return render(
            request,
            "base/connect_telegram.html",
            {
                "telegram_bot_link": telegram_bot_link,
                "link": telegram_bot_link,
                "bot_username": bot_username,
                "is_verified": False,
                "is_telegram_account_active_web": False,
                "skip_url": skip_url,
                "not_configured": not bool(telegram_bot_link),
            },
        )

    return render(
        request,
        "base/connect_telegram.html",
        {
            "telegram_bot_link": telegram_bot_link,
            "link": telegram_bot_link,
            "bot_username": bot_username,
            "is_verified": acc.telegram_verified,
            "is_telegram_account_active_web": acc.telegram_verified,
            "skip_url": skip_url,
            "not_configured": not bool(telegram_bot_link),
        },
    )


@csrf_exempt
@require_http_methods(["POST"])
def telegram_webhook(request: HttpRequest, bot_token: str) -> HttpResponse:
    if not constant_time_compare(bot_token, getattr(settings, "TELEGRAM_BOT_TOKEN_USERS", "")):
        return JsonResponse({"ok": False}, status=403)

    try:
        payload = json.loads(request.body.decode("utf-8"))
    except Exception:
        return JsonResponse({"ok": False}, status=400)

    ctx = _parse_update(payload)
    if not ctx.chat_id:
        return JsonResponse({"ok": True})

    # /start activate_<uuid>
    if ctx.start_payload and ctx.start_payload.startswith("activate_"):
        token_str = ctx.start_payload.replace("activate_", "").strip()
        try:
            uuid.UUID(token_str)
        except Exception:
            _send_text(ctx.chat_id, "Invalid activation token.")
            return JsonResponse({"ok": True})

        acc = TelegramAccount.objects.filter(activation_token=token_str).first()
        if not acc:
            _send_text(ctx.chat_id, "Activation token not found or already used.")
            return JsonResponse({"ok": True})

        if acc.telegram_verified and acc.telegram_id:
            _send_text(ctx.chat_id, "Account already linked.")
            return JsonResponse({"ok": True})

        acc.telegram_id = str(ctx.chat_id)
        acc.username = ctx.tg_username
        acc.first_name = ctx.first_name
        acc.last_name = ctx.last_name
        acc.language_code = ctx.lang
        acc.save(update_fields=["telegram_id", "username", "first_name", "last_name", "language_code"])

        cache.set(f"tg_bind:{ctx.chat_id}", acc.user_info_id, 15 * 60)
        _send_contact_request(ctx.chat_id, "Share your phone number to link your account.")
        return JsonResponse({"ok": True})

    # contact
    if ctx.phone:
        info_id = cache.get(f"tg_bind:{ctx.chat_id}")
        acc = None
        if not info_id:
            acc = TelegramAccount.objects.filter(telegram_id=str(ctx.chat_id), telegram_verified=False).first()
            if acc:
                info_id = acc.user_info_id

        if not info_id:
            _send_text(ctx.chat_id, "No active link session. Open the link from the site again.")
            return JsonResponse({"ok": True})

        phone = _norm_phone(ctx.phone)
        with transaction.atomic():
            info = AdditionalUserInfo.objects.select_for_update().get(id=info_id)
            info.phone = phone
            info.phone_verified = True
            info.save(update_fields=["phone", "phone_verified"])

            if not acc:
                acc = TelegramAccount.objects.select_for_update().get(user_info_id=info_id)
            acc.telegram_verified = True
            acc.activation_token = None
            acc.save(update_fields=["telegram_verified", "activation_token"])

        _send_text(ctx.chat_id, "Phone linked. You can return to the site.")
        return JsonResponse({"ok": True})

    _send_text(ctx.chat_id, "Tap the button and share your phone to finish linking.")
    return JsonResponse({"ok": True})