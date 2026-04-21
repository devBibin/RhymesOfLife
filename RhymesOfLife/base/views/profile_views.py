from datetime import date, datetime
from functools import lru_cache

from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.validators import ASCIIUsernameValidator
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.urls import reverse
from django.shortcuts import redirect, render
from django.utils.dates import MONTHS
from django.utils.translation import gettext as _
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.debug import sensitive_post_parameters
from django.views.decorators.http import require_http_methods

from ..models import (
    SYNDROME_STATUS_CHOICES,
    SYNDROME_STATUS_DOCTOR_CONFIRMED,
    SYNDROME_STATUS_DOCTOR_UNCONFIRMED,
    SYNDROME_STATUS_GENETIC_CONFIRMED,
    SYNDROMES_WITH_GENETIC_CONFIRMATION,
    get_syndrome_choices,
)
from ..utils.files import validate_image_upload
from ..utils.onboarding import resolve_post_onboarding_redirect
from ..models import TelegramAccount
from ..views.telegram_views import _get_bot_username

User = get_user_model()
username_validator = ASCIIUsernameValidator()

MAX_AVATAR_SIZE_BYTES = 10 * 1024 * 1024
MAX_AVATAR_DIMENSION = 4096
ALLOWED_IMAGE_MIMES = {"image/jpeg", "image/png", "image/webp"}
ALLOWED_IMAGE_FORMATS = {"JPEG", "PNG", "WEBP"}


@lru_cache(maxsize=1)
def syndrome_choices():
    return [(c, n) for c, n in get_syndrome_choices()]


def _syndrome_status_rows(info):
    status_map = getattr(info, "syndrome_statuses", None) or {}
    legacy_selected = set(getattr(info, "syndromes", None) or [])
    legacy_genetic = set(getattr(info, "confirmed_syndromes", None) or [])
    rows = []

    for code, label in syndrome_choices():
        statuses = list(status_map.get(code) or [])
        if not statuses:
            if code in legacy_genetic:
                statuses = [SYNDROME_STATUS_GENETIC_CONFIRMED]
            elif code in legacy_selected:
                statuses = [SYNDROME_STATUS_DOCTOR_UNCONFIRMED]
        rows.append({
            "code": code,
            "label": label,
            "statuses": statuses,
            "allow_genetic": code in SYNDROMES_WITH_GENETIC_CONFIRMATION,
        })
    return rows


def _parse_birth_date(day: str | None, month: str | None, year: str | None):
    if not (day and month and year):
        return None
    try:
        return datetime(int(year), int(month), int(day)).date()
    except ValueError:
        return "invalid"


def _clean_about(text: str | None, limit: int = 500) -> str:
    text = (text or "").strip()
    return text[:limit] if len(text) > limit else text


def _clean_required_profile_text(text: str | None) -> str:
    text = (text or "").strip()
    return "" if text.lower() in {"none", "null"} else text


def _profile_edit_context(info, months_list, year_range, day_range, tg_ctx, **extra):
    profile_needs_completion = not (
        _clean_required_profile_text(getattr(info, "first_name", None))
        and _clean_required_profile_text(getattr(info, "last_name", None))
        and _clean_required_profile_text(getattr(info, "email", None))
        and getattr(info, "birth_date", None)
    )
    ctx = {
        "info": info,
        "current_username": getattr(getattr(info, "user", None), "username", ""),
        "profile_needs_completion": profile_needs_completion,
        "syndrome_choices": syndrome_choices(),
        "syndrome_status_rows": _syndrome_status_rows(info),
        "syndrome_status_choices": SYNDROME_STATUS_CHOICES,
        "status_doctor_confirmed": SYNDROME_STATUS_DOCTOR_CONFIRMED,
        "status_doctor_unconfirmed": SYNDROME_STATUS_DOCTOR_UNCONFIRMED,
        "status_genetic_confirmed": SYNDROME_STATUS_GENETIC_CONFIRMED,
        "months_list": months_list,
        "year_range": year_range,
        "day_range": day_range,
        **tg_ctx,
    }
    ctx.update(extra)
    return ctx


@login_required
@require_http_methods(["GET"])
def profile_view(request, username=None):
    if username and username != request.user.username:
        return redirect("public_profile", username=username)

    user = request.user
    info = getattr(user, "additional_info", None)
    acc = getattr(info, "telegram_account", None)
    return render(
        request,
        "base/profile.html",
        {
            "user_profile": user,
            "info": info,
            "editable": True,
            "syndrome_choices": syndrome_choices(),
            "syndrome_status_rows": _syndrome_status_rows(info),
            "status_doctor_confirmed": SYNDROME_STATUS_DOCTOR_CONFIRMED,
            "status_doctor_unconfirmed": SYNDROME_STATUS_DOCTOR_UNCONFIRMED,
            "status_genetic_confirmed": SYNDROME_STATUS_GENETIC_CONFIRMED,
            "tg_is_verified": bool(getattr(acc, "telegram_verified", False)),
            "tg_username": getattr(acc, "username", None),
        },
    )


@login_required
@require_http_methods(["GET", "POST"])
@csrf_protect
@never_cache
@sensitive_post_parameters(
    "username",
    "first_name",
    "last_name",
    "email",
    "day",
    "month",
    "year",
    "about_me",
    "syndromes",
    "confirmed_syndromes",
    "syndrome_status",
    "syndromes_other",
)
def profile_edit_view(request):
    info = request.user.additional_info
    user = request.user

    months_list = list(MONTHS.items())
    today = date.today()
    year_range = list(range(today.year - 100, today.year + 1))[::-1]
    day_range = range(1, 32)

    acc, created = TelegramAccount.objects.get_or_create(user_info=info)
    bot_username = _get_bot_username()
    telegram_bot_link = (
        f"https://t.me/{bot_username}?start=activate_{acc.activation_token}"
        if bot_username and acc.activation_token
        else None
    )
    tg_ctx = {
        "tg_is_verified": acc.telegram_verified,
        "tg_username": acc.username,
        "tg_link": telegram_bot_link,
        "tg_not_configured": not bool(bot_username),
        "tg_bot_username": bot_username,
    }

    if request.method == "POST":
        try:
            new_username = (request.POST.get("username") or "").strip()
            info.first_name = _clean_required_profile_text(request.POST.get("first_name"))
            info.last_name = _clean_required_profile_text(request.POST.get("last_name"))
            info.about_me = _clean_about(request.POST.get("about_me"))
            user.username = new_username

            new_email = _clean_required_profile_text(request.POST.get("email")).lower()

            try:
                username_validator(new_username)
            except ValidationError as exc:
                return render(
                    request,
                    "base/profile_edit.html",
                    _profile_edit_context(
                        info,
                        months_list,
                        year_range,
                        day_range,
                        tg_ctx,
                        error=exc.messages[0],
                    ),
                    status=400,
                )

            if User.objects.filter(username=new_username).exclude(pk=user.pk).exists():
                return render(
                    request,
                    "base/profile_edit.html",
                    _profile_edit_context(
                        info,
                        months_list,
                        year_range,
                        day_range,
                        tg_ctx,
                        error=_("A user with that username already exists."),
                    ),
                    status=400,
                )

            bd = _parse_birth_date(request.POST.get("day"), request.POST.get("month"), request.POST.get("year"))
            if bd == "invalid":
                return render(
                    request,
                    "base/profile_edit.html",
                    _profile_edit_context(
                        info,
                        months_list,
                        year_range,
                        day_range,
                        tg_ctx,
                        error=_("Invalid date of birth."),
                    ),
                    status=400,
                )
            info.birth_date = bd

            allowed_statuses = {code for code, _label in SYNDROME_STATUS_CHOICES}
            selected = []
            confirmed = []
            syndrome_statuses = {}
            for code, _label in syndrome_choices():
                values = []
                for status in request.POST.getlist(f"syndrome_status_{code}"):
                    if status not in allowed_statuses:
                        continue
                    if status == SYNDROME_STATUS_GENETIC_CONFIRMED and code not in SYNDROMES_WITH_GENETIC_CONFIRMATION:
                        continue
                    if status not in values:
                        values.append(status)

                if SYNDROME_STATUS_DOCTOR_CONFIRMED in values and SYNDROME_STATUS_DOCTOR_UNCONFIRMED in values:
                    values = [v for v in values if v != SYNDROME_STATUS_DOCTOR_UNCONFIRMED]
                if SYNDROME_STATUS_GENETIC_CONFIRMED in values and SYNDROME_STATUS_DOCTOR_UNCONFIRMED in values:
                    values = [v for v in values if v != SYNDROME_STATUS_DOCTOR_UNCONFIRMED]

                if values:
                    selected.append(code)
                    syndrome_statuses[code] = values
                if SYNDROME_STATUS_GENETIC_CONFIRMED in values:
                    confirmed.append(code)

            info.syndromes = selected
            info.confirmed_syndromes = confirmed
            info.syndrome_statuses = syndrome_statuses
            info.syndromes_other = (request.POST.get("syndromes_other") or "").strip()[:255]

            if new_email:
                exists = User.objects.filter(email=new_email).exclude(pk=request.user.pk).exists()
                if exists:
                    return render(
                        request,
                        "base/profile_edit.html",
                        _profile_edit_context(
                            info,
                            months_list,
                            year_range,
                            day_range,
                            tg_ctx,
                            error=_("This email is already registered."),
                        ),
                        status=400,
                    )
                if user.email != new_email:
                    user.email = new_email
                info.email = new_email

            delete_flag = request.POST.get("delete_avatar") == "1"
            image = request.FILES.get("avatar")

            if delete_flag:
                if info.avatar:
                    info.avatar.delete(save=False)
                info.avatar = None
            elif image:
                ok, err = validate_image_upload(
                    image,
                    max_size_bytes=MAX_AVATAR_SIZE_BYTES,
                    max_side_px=MAX_AVATAR_DIMENSION,
                    allowed_mimes=ALLOWED_IMAGE_MIMES,
                    allowed_formats=ALLOWED_IMAGE_FORMATS,
                    max_total_pixels=50_000_000,
                )
                if not ok:
                    return render(
                        request,
                        "base/profile_edit.html",
                        _profile_edit_context(
                            info,
                            months_list,
                            year_range,
                            day_range,
                            tg_ctx,
                            error=_(err),
                        ),
                        status=400,
                    )
                try:
                    image.seek(0)
                except Exception:
                    pass
                info.avatar = image

            if not (info.first_name and info.last_name and info.email and info.birth_date):
                return render(
                    request,
                    "base/profile_edit.html",
                    _profile_edit_context(
                        info,
                        months_list,
                        year_range,
                        day_range,
                        tg_ctx,
                        error=_("Please fill in username, first name, last name, email, and date of birth."),
                    ),
                    status=400,
                )

            try:
                user.full_clean(exclude=["password", "last_login", "date_joined", "first_name", "last_name"])
                info.full_clean()
            except ValidationError as e:
                msgs = []
                for field, errs in getattr(e, "message_dict", {"__all__": e.messages}).items():
                    msgs.extend(errs if isinstance(errs, (list, tuple)) else [errs])
                return render(
                    request,
                    "base/profile_edit.html",
                    _profile_edit_context(
                        info,
                        months_list,
                        year_range,
                        day_range,
                        tg_ctx,
                        error="; ".join(msgs) or _("Validation failed."),
                    ),
                    status=400,
                )

            user.save(update_fields=["username", "email"])
            info.save()
            messages.success(request, _("Profile has been updated."))
            return redirect(resolve_post_onboarding_redirect(request, default=reverse("my_profile"), consume=True))

        except Exception:
            return render(
                request,
                "base/profile_edit.html",
                _profile_edit_context(
                    info,
                    months_list,
                    year_range,
                    day_range,
                    tg_ctx,
                    error=_("Error while saving."),
                ),
                status=500,
            )

    return render(
        request,
        "base/profile_edit.html",
        _profile_edit_context(info, months_list, year_range, day_range, tg_ctx),
    )
