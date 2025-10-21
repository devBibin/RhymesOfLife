from typing import Optional

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.models import User
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect, render, get_object_or_404
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_http_methods
from django.views.decorators.debug import sensitive_post_parameters
from django.views.decorators.cache import never_cache

from ..models import PasswordResetCode
from ..utils.password_reset import (
    create_reset_code,
    send_code_email,
    send_code_telegram,
    _rate_allow,
    user_can_receive_telegram,
    resolve_user_by_identifier,
)


def _client_ip(request: HttpRequest) -> str:
    v = (request.META.get("HTTP_X_FORWARDED_FOR", "") or "").split(",")[0].strip()
    return v or request.META.get("REMOTE_ADDR", "") or ""


@require_http_methods(["GET", "POST"])
@csrf_protect
@never_cache
@sensitive_post_parameters("identifier", "channel")
def password_reset_request_view(request: HttpRequest) -> HttpResponse:
    if request.user.is_authenticated:
        return redirect("home")

    if request.method == "POST":
        identifier = (request.POST.get("identifier") or "").strip()
        channel = (request.POST.get("channel") or "email").strip()
        ip = _client_ip(request)

        if not identifier:
            messages.error(request, _("Enter your username or email."))
            return render(request, "base/reset_request.html")

        ip_window_sec = int(getattr(settings, "PASSWORD_RESET_RATE_LIMIT_PER_IP_MIN", 10)) * 60
        user_window_sec = int(getattr(settings, "PASSWORD_RESET_RATE_LIMIT_PER_USER_MIN", 10)) * 60
        ip_max = int(getattr(settings, "PASSWORD_RESET_RATE_LIMIT_IP_MAX_CALLS", 5))
        user_max = int(getattr(settings, "PASSWORD_RESET_RATE_LIMIT_USER_MAX_CALLS", 3))

        if not _rate_allow("ip", ip, max_calls=ip_max, window_sec=ip_window_sec):
            messages.error(request, _("Too many requests. Try again later."))
            return render(request, "base/reset_request.html")

        user: Optional[User] = resolve_user_by_identifier(identifier)

        if user:
            if channel not in ("email", "telegram"):
                channel = "email"
            if channel == "telegram" and not user_can_receive_telegram(user):
                messages.error(request, _("Telegram is not linked to this account."))
                return render(request, "base/reset_request.html")

            if not _rate_allow("user", str(user.id), max_calls=user_max, window_sec=user_window_sec):
                messages.error(request, _("Too many requests for this account. Try again later."))
                return render(request, "base/reset_request.html")

            try:
                rec = create_reset_code(
                    user,
                    channel,
                    ip=ip,
                    ua=request.META.get("HTTP_USER_AGENT", ""),
                )
                if channel == "email":
                    send_code_email(user, rec.code)
                else:
                    send_code_telegram(user, rec.code)
                request.session["pwdreset_user"] = user.id
            except Exception:
                messages.error(request, _("Failed to send a code. Please try again later."))
                return render(request, "base/reset_request.html")

        messages.success(request, _("If the account exists, a code has been sent."))
        return redirect("password_reset_verify")

    return render(request, "base/reset_request.html")


@require_http_methods(["GET", "POST"])
@csrf_protect
@never_cache
@sensitive_post_parameters("code")
def password_reset_verify_view(request: HttpRequest) -> HttpResponse:
    if request.user.is_authenticated:
        return redirect("home")

    user_id = request.session.get("pwdreset_user")
    if request.method == "POST":
        code = (request.POST.get("code") or "").strip()
        if not user_id or not code:
            messages.error(request, _("Invalid code."))
            return render(request, "base/reset_verify.html")
        rec = PasswordResetCode.objects.filter(user_id=user_id).order_by("-created_at").first()
        if not rec or not rec.is_active():
            messages.error(request, _("Code is expired or invalid."))
            return render(request, "base/reset_verify.html")
        if rec.code != code:
            rec.attempts_left = max(rec.attempts_left - 1, 0)
            rec.save(update_fields=["attempts_left"])
            messages.error(request, _("Incorrect code."))
            return render(request, "base/reset_verify.html")
        rec.used_at = timezone.now()
        rec.save(update_fields=["used_at"])
        request.session["pwdreset_verified"] = True
        return redirect("password_reset_new")
    return render(request, "base/reset_verify.html")


@require_http_methods(["GET", "POST"])
@csrf_protect
@never_cache
@sensitive_post_parameters("password1", "password2")
def password_reset_new_view(request: HttpRequest) -> HttpResponse:
    from django.contrib.auth.hashers import make_password

    if request.user.is_authenticated:
        return redirect("home")

    user_id = request.session.get("pwdreset_user")
    verified = request.session.get("pwdreset_verified")
    if not (user_id and verified):
        return redirect("password_reset_request")

    if request.method == "POST":
        p1 = request.POST.get("password1") or ""
        p2 = request.POST.get("password2") or ""
        if not p1 or p1 != p2:
            messages.error(request, _("Passwords don't match."))
            return render(request, "base/reset_new.html")

        user = get_object_or_404(User, pk=user_id)
        user.password = make_password(p1)
        user.save(update_fields=["password"])
        request.session.pop("pwdreset_user", None)
        request.session.pop("pwdreset_verified", None)
        messages.success(request, _("Password has been reset. You can sign in now."))
        return redirect("login")

    return render(request, "base/reset_new.html")
