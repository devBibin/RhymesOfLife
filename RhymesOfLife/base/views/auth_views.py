from django.contrib.auth import login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.utils.http import urlsafe_base64_decode
from django.utils.encoding import force_str
from django.contrib.auth.tokens import default_token_generator
from django.contrib.auth.models import User
from django.contrib.auth.hashers import make_password
from django.utils.translation import gettext_lazy as _
from django.db import transaction

from ..models import AdditionalUserInfo
from ..utils.logging import get_app_logger, get_security_logger

log = get_app_logger(__name__)
seclog = get_security_logger()


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
    user = User.objects.create(
        username=username,
        email=email,
        password=make_password(raw_password),
    )
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
        messages.success(
            request,
            _("Registration was successful! A confirmation email will arrive shortly.")
        )
        return redirect("verify_prompt")
    return render(request, "base/register.html", context)


@require_http_methods(["GET", "POST"])
def login_view(request):
    if request.method == "POST":
        form = AuthenticationForm(data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            seclog.info("Login success: user_id=%s username=%s", user.id, user.username)
            return redirect("home")
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
        info.save()
        login(request, user)
        seclog.info("Email verified: user_id=%s", user.id)
        return redirect("profile_onboarding")

    messages.error(request, _("Email verification failed or token is invalid."))
    seclog.warning("Email verification failed: uid=%s", uidb64)
    return render(request, "base/verification_failed.html")


@login_required
@require_http_methods(["POST"])
def request_verification_view(request):
    info = getattr(request.user, "additional_info", None)
    if info is None:
        info = AdditionalUserInfo.objects.create(user=request.user)
    info.ready_for_verification = True
    info.save()
    messages.success(
        request,
        _("A verification email has been sent. Please confirm your account.")
    )
    log.info("Verification requested: user_id=%s", request.user.id)
    return redirect("home")


@require_http_methods(["GET", "POST"])
def home_view(request):
    is_authed = request.user.is_authenticated
    user = request.user if is_authed else None

    show_verification_notice = (
        is_authed
        and hasattr(user, "additional_info")
        and not user.additional_info.is_verified
    )

    context = {
        "show_verification_notice": show_verification_notice,
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
                return render(request, "base/home.html", context)
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
                seclog.info("Login success via home: user_id=%s", user.id)
                return redirect("home")
            error = _("Invalid username or password.")
            messages.error(request, error)
            context["login_error"] = error
            seclog.warning("Login failed via home: username=%s", request.POST.get("username"))
            return render(request, "base/home.html", context)

    return render(request, "base/home.html", context)
