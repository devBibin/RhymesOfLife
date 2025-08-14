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


# ---------- Shared helpers ----------

def _validate_signup_input(username: str, email: str, password1: str, password2: str):
    """
    Returns (error_message | None). Keeps messages i18n-ready.
    """
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
    """
    Creates a User and its AdditionalUserInfo in one atomic step.
    """
    user = User.objects.create(
        username=username,
        email=email,
        password=make_password(raw_password),
    )
    info, _ = AdditionalUserInfo.objects.get_or_create(user=user)
    info.email = email
    info.ready_for_verification = True
    info.save()
    return user


# ---------- Views ----------

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
            context["error"] = error
            return render(request, "base/register.html", context)

        _create_user_with_profile(username, email, password1)
        messages.success(
            request,
            _("Registration was successful! A confirmation email will arrive shortly.")
        )
        return redirect("login")

    return render(request, "base/register.html", context)


@require_http_methods(["GET", "POST"])
def login_view(request):
    if request.method == "POST":
        form = AuthenticationForm(data=request.POST)
        if form.is_valid():
            login(request, form.get_user())
            return redirect("home")
        messages.error(request, _("Invalid username or password."))
    else:
        form = AuthenticationForm()

    return render(request, "base/login.html", {"form": form})


@require_http_methods(["POST"])
def logout_view(request):
    logout(request)
    return redirect("login")


@require_http_methods(["GET"])
def verify_email_view(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = get_object_or_404(User, pk=uid)
    except Exception:
        user = None

    if user and default_token_generator.check_token(user, token):
        info, _ = AdditionalUserInfo.objects.get_or_create(user=user)
        info.is_verified = True
        info.save()
        login(request, user)
        return redirect("my_profile")

    return render(request, "base/verification_failed.html")


@login_required
@require_http_methods(["POST"])
def request_verification_view(request):
    info, _ = AdditionalUserInfo.objects.get_or_create(user=request.user)
    info.ready_for_verification = True
    info.save()
    messages.success(
        request,
        _("A verification email has been sent. Please confirm your account.")
    )
    return redirect("home")


# --- Home: available to all + tabbed Sign Up / Log In for guests
@require_http_methods(["GET", "POST"])
def home_view(request):
    is_authed = getattr(request.user, "is_authenticated", False)
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
                context["reg_error"] = error
                return render(request, "base/home.html", context)

            _create_user_with_profile(username, email, password1)
            messages.success(
                request,
                _("Registration was successful! A confirmation email will arrive shortly.")
            )
            return redirect("login")

        if form_type == "login":
            context["active_tab"] = "login"
            context["login_values"] = {"username": request.POST.get("username", "").strip()}
            form = AuthenticationForm(data=request.POST)
            if form.is_valid():
                login(request, form.get_user())
                return redirect("home")

            context["login_error"] = _("Invalid username or password.")
            return render(request, "base/home.html", context)

    return render(request, "base/home.html", context)
