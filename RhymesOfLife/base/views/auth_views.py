from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.hashers import make_password
from django.contrib.auth.models import User
from django.contrib.auth.tokens import default_token_generator
from django.db import transaction
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.utils.encoding import force_str
from django.utils.http import urlsafe_base64_decode
from django.utils.translation import gettext_lazy as _, activate
from django.views.decorators.http import require_http_methods, require_GET
from django.contrib.auth.decorators import login_required
import random

from ..models import AdditionalUserInfo
from ..utils.logging import get_app_logger, get_security_logger
from ..utils.phone_calls import (
    initiate_zvonok_verification,
    poll_zvonok_status,
    normalize_phone_e164_with_plus,
)

try:
    from django.utils.translation import LANGUAGE_SESSION_KEY as LANG_SESSION_KEY
except Exception:
    LANG_SESSION_KEY = "django_language"

log = get_app_logger(__name__)
seclog = get_security_logger()


def _apply_user_language(request, user):
    lang = getattr(getattr(user, "additional_info", None), "language", None) or settings.LANGUAGE_CODE
    activate(lang)
    request.session[LANG_SESSION_KEY] = lang
    return lang


def _validate_signup_input(username: str, email: str, password1: str, password2: str):
    if not username or not email or not password1:
        return _("Please fill in all fields.")
    if password1 != password2:
        return _("Passwords don't match.")
    if User.objects.filter(username=username).exists():
        return _("A user with that username already exists.")
    if User.objects.filter(email=email).exists():
        return _("This email is already registered.")
    return None


@transaction.atomic
def _create_user_with_profile(username: str, email: str, raw_password: str) -> User:
    user = User.objects.create(username=username, email=email, password=make_password(raw_password))
    info = AdditionalUserInfo.objects.create(user=user, email=email, ready_for_verification=True)
    info.save()
    log.info("User created: username=%s email=%s id=%s", username, email, user.id)
    seclog.info("Signup: user_id=%s email=%s", user.id, email)
    return user


@require_http_methods(["GET", "POST"])
def register_view(request):
    context = {"values": {}}
    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        email = request.POST.get("email", "").strip().lower()
        password1 = request.POST.get("password1", "")
        password2 = request.POST.get("password2", "")
        context["values"] = {"username": username, "email": email}
        error = _validate_signup_input(username, email, password1, password2)
        if error:
            messages.error(request, error)
            context["error"] = error
            log.warning("Signup validation failed: username=%s email=%s reason=%s", username, email, error)
            return render(request, "base/register.html", context)
        _create_user_with_profile(username, email, password1)
        messages.success(request, _("Registration was successful! A confirmation email will arrive shortly."))
        return redirect("verify_prompt")
    return render(request, "base/register.html", context)


@require_http_methods(["GET", "POST"])
def login_view(request):
    if request.method == "POST":
        form = AuthenticationForm(data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            lang = _apply_user_language(request, user)
            seclog.info("Login success: user_id=%s username=%s", user.id, user.username)
            response = redirect("home")
            response.set_cookie(settings.LANGUAGE_COOKIE_NAME, lang, samesite="Lax")
            return response
        messages.error(request, _("Invalid username or password."))
        seclog.warning("Login failed: username=%s ip=%s", request.POST.get("username"), request.META.get("REMOTE_ADDR"))
    else:
        form = AuthenticationForm()
    return render(request, "base/login.html", {"form": form})


@require_http_methods(["POST"])
def logout_view(request):
    uid = getattr(request.user, "id", None)
    logout(request)
    seclog.info("Logout: user_id=%s", uid)
    return redirect("login")


@require_http_methods(["GET"])
def verify_prompt_view(request):
    return render(request, "base/verify_prompt.html")


@login_required
@require_http_methods(["POST"])
def request_verification_view(request):
    info = getattr(request.user, "additional_info", None)
    if info is None:
        info = AdditionalUserInfo.objects.create(user=request.user)
    info.ready_for_verification = True
    info.save(update_fields=["ready_for_verification"])
    messages.success(request, _("A verification email has been sent. Please confirm your account."))
    return redirect("verify_prompt")


@require_http_methods(["GET"])
def verify_email_view(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = get_object_or_404(User, pk=uid)
    except Exception:
        user = None
    if user and default_token_generator.check_token(user, token):
        info = getattr(user, "additional_info", None)
        if info is None:
            info = AdditionalUserInfo.objects.create(user=user)
        info.is_verified = True
        info.save(update_fields=["is_verified"])
        login(request, user)
        lang = _apply_user_language(request, user)
        seclog.info("Email verified: user_id=%s", user.id)
        response = redirect("connect_telegram")
        response.set_cookie(settings.LANGUAGE_COOKIE_NAME, lang, samesite="Lax")
        return response
    messages.error(request, _("Email verification failed or token is invalid."))
    seclog.warning("Email verification failed: uid=%s", uidb64)
    return render(request, "base/verification_failed.html")


@login_required
@require_http_methods(["GET", "POST"])
def phone_enter_view(request):
    info = request.user.additional_info
    if info.phone_verified:
        consents_ok = info.tos_accepted and info.privacy_accepted and info.data_processing_accepted
        if not consents_ok:
            return redirect("consents")
        return redirect("home")
    context = {}
    if request.method == "POST":
        phone = request.POST.get("phone", "").strip()
        if not phone:
            context["error"] = _("Enter phone number.")
            return render(request, "base/enter_phone_number.html", context)
        normalized = normalize_phone_e164_with_plus(phone)
        pin = f"{random.randint(1000, 9999)}"
        resp = initiate_zvonok_verification(normalized, pincode=pin)
        if not resp.get("ok"):
            context["error"] = resp.get("message") or _("Failed to initiate call.")
            return render(request, "base/enter_phone_number.html", context)
        info.phone = normalized
        info.save(update_fields=["phone"])
        request.session["call_number"] = resp.get("call_number") or getattr(settings, "ZVONOK_STATIC_GATEWAY", "")
        return redirect("phone_wait")
    return render(request, "base/enter_phone_number.html", context)


@login_required
@require_http_methods(["GET"])
def phone_wait_view(request):
    info = request.user.additional_info
    call_number = request.session.get("call_number") or "-"
    return render(request, "base/wait_for_phone_call.html", {"phone": info.phone, "call_number": call_number})


@login_required
@require_GET
def phone_status_api(request):
    info, _ = AdditionalUserInfo.objects.get_or_create(user=request.user)

    if not info.phone:
        return JsonResponse({"status": "error", "message": str(_("No phone number set."))}, status=400)

    if info.phone_verified:
        return JsonResponse({"status": "done", "next": "/consents/"})

    try:
        api = poll_zvonok_status(info.phone)
    except Exception:
        log.exception("Phone status provider error: user_id=%s", request.user.id)
        return JsonResponse({"status": "error", "message": str(_("Provider error"))}, status=502)

    if not api.get("ok"):
        return JsonResponse({"status": "error", "message": api.get("message") or str(_("Provider error"))}, status=502)

    if api.get("verified"):
        info.phone_verified = True
        info.save(update_fields=["phone_verified"])
        return JsonResponse({"status": "success", "next": "/consents/"})

    return JsonResponse({
        "status": "pending",
        "dial_status": api.get("dial_status_display") or ""
    })


@login_required
@require_http_methods(["POST"])
def phone_change_view(request):
    info = request.user.additional_info
    info.phone = None
    info.phone_verified = False
    info.save(update_fields=["phone", "phone_verified"])
    request.session.pop("call_number", None)
    return redirect("phone_enter")


@login_required
@require_http_methods(["GET", "POST"])
def consents_view(request):
    info = request.user.additional_info
    if request.method == "POST":
        t = bool(request.POST.get("tos"))
        p = bool(request.POST.get("privacy"))
        d = bool(request.POST.get("data"))
        if not (t and p and d):
            return render(request, "base/consents.html", {"error": _("Please accept all items.")})
        info.tos_accepted = True
        info.privacy_accepted = True
        info.data_processing_accepted = True
        info.consents_accepted_at = timezone.now()
        info.save(update_fields=["tos_accepted", "privacy_accepted", "data_processing_accepted", "consents_accepted_at"])
        return redirect("profile_edit")
    return render(request, "base/consents.html")


@require_http_methods(["GET", "POST"])
def home_public_view(request):
    is_authed = request.user.is_authenticated
    user = request.user if is_authed else None

    def has_consents(i):
        return i.tos_accepted and i.privacy_accepted and i.data_processing_accepted

    def profile_complete(i):
        return bool(i.first_name and i.last_name and i.email and i.birth_date)

    if is_authed and hasattr(user, "additional_info"):
        info = user.additional_info
        current_name = getattr(getattr(request, "resolver_match", None), "url_name", "")

        if info.is_verified and not info.phone_verified and current_name not in {
            "connect_telegram", "phone_enter", "phone_wait", "phone_status_api", "phone_change"
        }:
            return redirect("connect_telegram")

        if info.is_verified and info.phone_verified and not has_consents(info) and current_name != "consents":
            return redirect("consents")

        if info.is_verified and info.phone_verified and has_consents(info) and not profile_complete(info) and current_name != "profile_edit":
            return redirect("profile_edit")

    context = {
        "show_verification_notice": is_authed and hasattr(user, "additional_info") and not user.additional_info.is_verified if is_authed else False,
        "active_tab": "signup",
        "reg_values": {},
        "login_values": {},
    }
    if request.method == "POST":
        if is_authed:
            messages.info(request, _("You are already signed in."))
            return redirect("home")
        form_type = request.POST.get("form_type")
        if form_type == "signup":
            username = request.POST.get("username", "").strip()
            email = request.POST.get("email", "").strip().lower()
            password1 = request.POST.get("password1", "")
            password2 = request.POST.get("password2", "")
            context["active_tab"] = "signup"
            context["reg_values"] = {"username": username, "email": email}
            error = _validate_signup_input(username, email, password1, password2)
            if error:
                messages.error(request, error)
                context["reg_error"] = error
                log.warning("Home signup validation failed: username=%s email=%s reason=%s", username, email, error)
                return render(request, "base/home_public.html", context)
            _create_user_with_profile(username, email, password1)
            messages.success(request, _("Registration was successful! A confirmation email will arrive shortly."))
            return redirect("verify_prompt")
        if form_type == "login":
            context["active_tab"] = "login"
            context["login_values"] = {"username": request.POST.get("username", "").strip()}
            form = AuthenticationForm(data=request.POST)
            if form.is_valid():
                user = form.get_user()
                login(request, user)
                lang = _apply_user_language(request, user)
                seclog.info("Login success via home: user_id=%s", user.id)
                response = redirect("home")
                response.set_cookie(settings.LANGUAGE_COOKIE_NAME, lang, samesite="Lax")
                return response
            error = _("Invalid username or password.")
            messages.error(request, error)
            context["login_error"] = error
            seclog.warning("Login failed via home: username=%s", request.POST.get("username"))
            return render(request, "base/home_public.html", context)

    return render(request, "base/home_public.html", context)


@require_http_methods(["GET"])
def info_ndst(request):
    return render(request, "base/info/ndst.html")


@require_http_methods(["GET"])
def info_sed(request):
    return render(request, "base/info/sed.html")


@require_http_methods(["GET"])
def info_marfan(request):
    return render(request, "base/info/marfan.html")


@require_http_methods(["GET"])
def info_sld(request):
    return render(request, "base/info/sld.html")
