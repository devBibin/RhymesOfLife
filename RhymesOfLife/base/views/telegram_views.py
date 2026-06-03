from __future__ import annotations

import json
import uuid
from dataclasses import dataclass

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.cache import cache
from django.db import transaction
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils.crypto import constant_time_compare
from django.utils.translation import gettext as _
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_exempt, csrf_protect
from django.views.decorators.http import require_http_methods
from urllib.parse import quote

from ..models import AdditionalUserInfo, TelegramAccount
from ..utils.onboarding import resolve_post_onboarding_redirect
from ..utils.telegram import get_bot_username, send_bot_message


def _api_send(method: str, payload: dict) -> None:
    token = getattr(settings, "TELEGRAM_BOT_TOKEN_USERS", "")
    if not token:
        return
    if method != "sendMessage":
        return
    send_bot_message(
        token=token,
        chat_id=payload["chat_id"],
        text=payload["text"],
        parse_mode=payload.get("parse_mode"),
        disable_web_page_preview=payload.get("disable_web_page_preview", True),
        reply_markup=payload.get("reply_markup"),
    )


def _send_text(chat_id: int, text: str) -> None:
    _api_send("sendMessage", {"chat_id": chat_id, "text": text, "disable_web_page_preview": True})


def _send_contact_request(chat_id: int, text: str) -> None:
    keyboard = {
        "keyboard": [[{"text": _("Share phone"), "request_contact": True}]],
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
        return str(name).strip().lstrip("@")

    token = getattr(settings, "TELEGRAM_BOT_TOKEN_USERS", "")
    if not token:
        return None
    name = get_bot_username(token)
    if name:
        normalized = str(name).strip().lstrip("@")
        cache.set("tg_bot_username", normalized, 24 * 60 * 60)
        return normalized
    return None


def _build_bot_links(bot_username: str | None, activation_token) -> tuple[str | None, str |None]:
    if not bot_username or not activation_token:
        return None, None
    start_payload = quote(f"activate_{activation_token}")
    return (
        f"https://t.me/{bot_username}?start={start_payload}",
        f"tg://resolve?domain={bot_username}&start={start_payload}",
    )


def _make_bot_link_for(info: AdditionalUserInfo) -> tuple[str | None, str | None, str | None]:
    acc, created = TelegramAccount.objects.get_or_create(user_info=info)
    if not acc.activation_token:
        acc.activation_token = uuid.uuid4()
        acc.save(update_fields=["activation_token"])
    bot_username = _get_bot_username()
    web_link, app_link = _build_bot_links(bot_username, acc.activation_token)
    return bot_username, web_link, app_link


@dataclass
class UpdateCtx:
    chat_id: int | None
    from_user_id: int | None
    text: str | None
    start_payload: str | None
    phone: str | None
    contact_user_id: int | None
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
        from_user_id=frm.get("id"),
        text=text,
        start_payload=payload,
        phone=phone,
        contact_user_id=contact.get("user_id"),
        tg_username=frm.get("username"),
        first_name=frm.get("first_name"),
        last_name=frm.get("last_name"),
        lang=frm.get("language_code"),
    )


def _norm_phone(phone: str) -> str:
    p = (phone or "").strip()
    return p if p.startswith("+") else f"+{p}" if p else p


def _pending_bind_info_id(chat_id: int) -> int | None:
    info_id = cache.get(f"tg_bind:{chat_id}")
    if info_id:
        return info_id
    acc = TelegramAccount.objects.filter(telegram_id=str(chat_id), telegram_verified=False).first()
    return acc.user_info_id if acc else None


def _claim_telegram_chat(acc: TelegramAccount, ctx: UpdateCtx) -> bool:
    chat_id = str(ctx.chat_id)
    previous = (
        TelegramAccount.objects.select_for_update()
        .filter(telegram_id=chat_id)
        .exclude(pk=acc.pk)
        .first()
    )
    if previous:
        if previous.telegram_verified and previous.user_info_id != acc.user_info_id:
            return False
        previous.telegram_id = None
        previous.username = None
        previous.first_name = None
        previous.last_name = None
        previous.language_code = None
        previous.telegram_verified = False
        previous.activation_token = uuid.uuid4()
        previous.save(
            update_fields=[
                "telegram_id",
                "username",
                "first_name",
                "last_name",
                "language_code",
                "telegram_verified",
                "activation_token",
                "updated_at",
            ]
        )

    acc.telegram_id = chat_id
    acc.username = ctx.tg_username
    acc.first_name = ctx.first_name
    acc.last_name = ctx.last_name
    acc.language_code = ctx.lang
    acc.save(update_fields=["telegram_id", "username", "first_name", "last_name", "language_code", "updated_at"])
    return True


@login_required
@require_http_methods(["GET", "POST"])
@csrf_protect
@never_cache
def connect_telegram_view(request: HttpRequest) -> HttpResponse:
    user_info = request.user.additional_info
    acc, created = TelegramAccount.objects.get_or_create(user_info=user_info)

    bot_username, telegram_bot_link, telegram_bot_app_link = _make_bot_link_for(user_info)
    skip_url = reverse("phone_enter")

    if request.method == "POST":
        acc.refresh_from_db()
        if acc.telegram_verified and user_info.phone_verified:
            return redirect(resolve_post_onboarding_redirect(request, consume=True))
        return render(
            request,
            "base/connect_telegram.html",
            {
                "telegram_bot_link": telegram_bot_link,
                "telegram_bot_app_link": telegram_bot_app_link,
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
            "telegram_bot_app_link": telegram_bot_app_link,
            "link": telegram_bot_link,
            "bot_username": bot_username,
            "is_verified": acc.telegram_verified,
            "is_telegram_account_active_web": acc.telegram_verified,
            "skip_url": skip_url,
            "not_configured": not bool(telegram_bot_link),
        },
    )


@login_required
@require_http_methods(["POST"])
@csrf_protect
@never_cache
def telegram_unlink_view(request: HttpRequest) -> HttpResponse:
    info = request.user.additional_info
    acc, created = TelegramAccount.objects.get_or_create(user_info=info)

    old_chat_id = acc.telegram_id

    acc.telegram_id = None
    acc.username = None
    acc.first_name = None
    acc.last_name = None
    acc.language_code = None
    acc.telegram_verified = False
    acc.activation_token = uuid.uuid4()
    acc.save(update_fields=[
        "telegram_id",
        "username",
        "first_name",
        "last_name",
        "language_code",
        "telegram_verified",
        "activation_token",
        "updated_at",
    ])

    if old_chat_id:
        cache.delete(f"tg_bind:{old_chat_id}")

    messages.success(request, _("Telegram has been unlinked."))
    return redirect("profile_edit")


@login_required
@require_http_methods(["POST"])
@csrf_protect
@never_cache
def telegram_regenerate_link_view(request: HttpRequest) -> HttpResponse:
    info = request.user.additional_info
    acc, created = TelegramAccount.objects.get_or_create(user_info=info)
    acc.activation_token = uuid.uuid4()
    acc.save(update_fields=["activation_token"])
    messages.success(request, _("New activation link generated."))
    return redirect("profile_edit")


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

    if ctx.start_payload and ctx.start_payload.startswith("activate_"):
        token_str = ctx.start_payload.replace("activate_", "").strip()
        try:
            uuid.UUID(token_str)
        except Exception:
            _send_text(ctx.chat_id, _("Invalid activation token."))
            return JsonResponse({"ok": True})

        acc = TelegramAccount.objects.filter(activation_token=token_str).select_related("user_info").first()
        if not acc:
            _send_text(ctx.chat_id, _("Activation token not found or already used."))
            return JsonResponse({"ok": True})

        with transaction.atomic():
            acc = TelegramAccount.objects.select_for_update().select_related("user_info").get(pk=acc.pk)
            claimed = _claim_telegram_chat(acc, ctx)
        if not claimed:
            _send_text(ctx.chat_id, _("This Telegram account is already linked to another profile. Please unlink it there first."))
            return JsonResponse({"ok": True})

        if acc.user_info.phone_verified:
            acc.telegram_verified = True
            acc.activation_token = None
            acc.save(update_fields=["telegram_verified", "activation_token"])
            _send_text(ctx.chat_id, _("Telegram account linked successfully."))
            return JsonResponse({"ok": True})

        cache.set(f"tg_bind:{ctx.chat_id}", acc.user_info_id, 15 * 60)
        _send_contact_request(ctx.chat_id, _("Share your phone number to link your account."))
        return JsonResponse({"ok": True})

    if ctx.phone:
        info_id = _pending_bind_info_id(ctx.chat_id)
        acc = None
        if not info_id:
            _send_text(ctx.chat_id, _("No active link session. Open the link from the site again."))
            return JsonResponse({"ok": True})

        expected_contact_user_id = str(ctx.from_user_id or ctx.chat_id or "")
        actual_contact_user_id = str(ctx.contact_user_id or "")
        if not actual_contact_user_id or actual_contact_user_id != expected_contact_user_id:
            _send_contact_request(
                ctx.chat_id,
                _("Please use the button below to share your own contact. Sending a typed number will not work."),
            )
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

        _send_text(ctx.chat_id, _("Phone linked. You can return to the site."))
        return JsonResponse({"ok": True})

    if _pending_bind_info_id(ctx.chat_id):
        _send_contact_request(ctx.chat_id, _("Use the button below to share your phone. Sending the number as a message will not work."))
        return JsonResponse({"ok": True})

    if ctx.text and ctx.text.startswith("/start"):
        _send_text(ctx.chat_id, _("Open the Telegram link from the site to start linking your account."))
        return JsonResponse({"ok": True})

    _send_text(ctx.chat_id, _("No active link session. Open the link from the site again."))
    return JsonResponse({"ok": True})
