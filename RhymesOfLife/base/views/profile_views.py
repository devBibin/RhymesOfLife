from datetime import date, datetime
import calendar

from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.shortcuts import redirect, render
from django.utils.translation import gettext as _
from django.views.decorators.http import require_http_methods

from ..models import get_syndrome_choices
from ..utils.files import validate_image_upload

User = get_user_model()

SYNDROME_CHOICES = [(c, n) for c, n in get_syndrome_choices()]

MAX_AVATAR_SIZE_BYTES = 10 * 1024 * 1024
MAX_AVATAR_DIMENSION = 4096
ALLOWED_IMAGE_MIMES = {"image/jpeg", "image/png", "image/webp"}
ALLOWED_IMAGE_FORMATS = {"JPEG", "PNG", "WEBP"}


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


@login_required
@require_http_methods(["GET"])
def profile_view(request, username=None):
    if username and username != request.user.username:
        return redirect("public_profile", username=username)

    user = request.user
    info = getattr(user, "additional_info", None)
    return render(
        request,
        "base/profile.html",
        {
            "user_profile": user,
            "info": info,
            "editable": True,
            "syndrome_choices": SYNDROME_CHOICES,
        },
    )


@login_required
@require_http_methods(["GET", "POST"])
def profile_edit_view(request):
    info = request.user.additional_info
    months_list = [(i, calendar.month_name[i]) for i in range(1, 13)]
    today = date.today()
    year_range = list(range(today.year - 100, today.year + 1))[::-1]
    day_range = range(1, 32)

    if request.method == "POST":
        try:
            info.first_name = request.POST.get("first_name", "").strip()
            info.last_name = request.POST.get("last_name", "").strip()
            info.about_me = _clean_about(request.POST.get("about_me"))

            new_email = (request.POST.get("email", "") or "").strip().lower()

            bd = _parse_birth_date(request.POST.get("day"), request.POST.get("month"), request.POST.get("year"))
            if bd == "invalid":
                return render(
                    request,
                    "base/profile_edit.html",
                    {
                        "info": info,
                        "syndrome_choices": SYNDROME_CHOICES,
                        "months_list": months_list,
                        "year_range": year_range,
                        "day_range": day_range,
                        "error": _("Invalid date of birth."),
                    },
                    status=400,
                )
            info.birth_date = bd

            selected = request.POST.getlist("syndromes")
            confirmed = request.POST.getlist("confirmed_syndromes")
            confirmed = [c for c in confirmed if c in selected]
            info.syndromes = selected
            info.confirmed_syndromes = confirmed

            if new_email:
                exists = User.objects.filter(email=new_email).exclude(pk=request.user.pk).exists()
                if exists:
                    return render(
                        request,
                        "base/profile_edit.html",
                        {
                            "info": info,
                            "syndrome_choices": SYNDROME_CHOICES,
                            "months_list": months_list,
                            "year_range": year_range,
                            "day_range": day_range,
                            "error": _("This email is already registered."),
                        },
                        status=400,
                    )
                if request.user.email != new_email:
                    request.user.email = new_email
                    request.user.save(update_fields=["email"])
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
                        {
                            "info": info,
                            "syndrome_choices": SYNDROME_CHOICES,
                            "months_list": months_list,
                            "year_range": year_range,
                            "day_range": day_range,
                            "error": _(err),
                        },
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
                    {
                        "info": info,
                        "syndrome_choices": SYNDROME_CHOICES,
                        "months_list": months_list,
                        "year_range": year_range,
                        "day_range": day_range,
                        "error": _("Please fill in first name, last name, email, and date of birth."),
                    },
                    status=400,
                )

            try:
                info.full_clean()
            except ValidationError as e:
                msgs = []
                for _, errs in getattr(e, "message_dict", {"__all__": e.messages}).items():
                    msgs.extend(errs if isinstance(errs, (list, tuple)) else [errs])
                return render(
                    request,
                    "base/profile_edit.html",
                    {
                        "info": info,
                        "syndrome_choices": SYNDROME_CHOICES,
                        "months_list": months_list,
                        "year_range": year_range,
                        "day_range": day_range,
                        "error": "; ".join(msgs) or _("Validation failed."),
                    },
                    status=400,
                )

            info.save()
            return redirect("my_profile")

        except Exception:
            return render(
                request,
                "base/profile_edit.html",
                {
                    "info": info,
                    "syndrome_choices": SYNDROME_CHOICES,
                    "months_list": months_list,
                    "year_range": year_range,
                    "day_range": day_range,
                    "error": _("Error while saving."),
                },
                status=500,
            )

    return render(
        request,
        "base/profile_edit.html",
        {
            "info": info,
            "syndrome_choices": SYNDROME_CHOICES,
            "months_list": months_list,
            "year_range": year_range,
            "day_range": day_range,
        },
    )
