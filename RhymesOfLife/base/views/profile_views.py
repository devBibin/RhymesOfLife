import calendar
from datetime import date, datetime

from django.shortcuts import get_object_or_404, render, redirect
from django.http import JsonResponse
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.utils.translation import gettext_lazy as _
from django.core.files.base import ContentFile

from ..models import AdditionalUserInfo, get_syndrome_choices
from ..utils.files import validate_image_upload

User = get_user_model()

SYNDROME_CHOICES = [(c, n) for c, n in get_syndrome_choices()]

MAX_AVATAR_SIZE_BYTES = 10 * 1024 * 1024
MAX_AVATAR_DIMENSION = 4096
ALLOWED_IMAGE_MIMES = {"image/jpeg", "image/png", "image/webp"}
ALLOWED_IMAGE_FORMATS = {"JPEG", "PNG", "WEBP"}


@login_required
@require_http_methods(["GET"])
def profile_view(request, username=None):
    if username:
        user = get_object_or_404(User.objects.select_related("additional_info"), username=username)
        editable = user == request.user
    else:
        user = request.user
        editable = True
    info = getattr(user, "additional_info", None)
    return render(
        request,
        "base/profile.html",
        {
            "user_profile": user,
            "info": info,
            "editable": editable,
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
            new_email = (request.POST.get("email", "") or "").strip().lower()

            day = request.POST.get("day")
            month = request.POST.get("month")
            year = request.POST.get("year")
            if day and month and year:
                try:
                    info.birth_date = datetime(int(year), int(month), int(day)).date()
                except ValueError:
                    return JsonResponse({"success": False, "error": _("Invalid date of birth.")}, status=400)
            else:
                info.birth_date = None

            selected = request.POST.getlist("syndromes")
            confirmed = request.POST.getlist("confirmed_syndromes")
            confirmed = [c for c in confirmed if c in selected]
            info.syndromes = selected
            info.confirmed_syndromes = confirmed

            if new_email:
                if User.objects.filter(email=new_email).exclude(pk=request.user.pk).exists():
                    return JsonResponse({"success": False, "error": _("This email is already registered.")}, status=400)
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
                    return JsonResponse({"success": False, "error": _(err)}, status=400)
                try:
                    image.seek(0)
                except Exception:
                    pass
                info.avatar = image

            from django.core.exceptions import ValidationError
            try:
                info.full_clean()
            except ValidationError as e:
                msgs = []
                for _, errs in getattr(e, "message_dict", {"__all__": e.messages}).items():
                    if isinstance(errs, (list, tuple)):
                        msgs.extend(errs)
                    else:
                        msgs.append(errs)
                return JsonResponse({"success": False, "error": "; ".join(msgs) or _("Validation failed.")}, status=400)

            info.save()
            return JsonResponse({"success": True})

        except Exception:
            return JsonResponse({"success": False, "error": _("Error while saving.")}, status=500)

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


@login_required
@require_http_methods(["GET", "POST"])
def profile_onboarding_view(request):
    info = request.user.additional_info
    months_list = [(i, calendar.month_name[i]) for i in range(1, 13)]
    today = date.today()
    year_range = list(range(today.year - 100, today.year + 1))[::-1]
    day_range = range(1, 32)

    if request.method == "POST":
        info.first_name = request.POST.get("first_name", "").strip()
        info.last_name = request.POST.get("last_name", "").strip()
        info.email = request.POST.get("email", "").strip()

        day = request.POST.get("day")
        month = request.POST.get("month")
        year = request.POST.get("year")
        if day and month and year:
            try:
                info.birth_date = datetime(int(year), int(month), int(day)).date()
            except ValueError:
                info.birth_date = None
        else:
            info.birth_date = None

        selected = request.POST.getlist("syndromes")
        confirmed = request.POST.getlist("confirmed_syndromes")
        confirmed = [c for c in confirmed if c in selected]
        info.syndromes = selected
        info.confirmed_syndromes = confirmed

        image = request.FILES.get("avatar")
        if image:
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
                    "base/profile_onboarding.html",
                    {
                        "info": info,
                        "syndrome_choices": SYNDROME_CHOICES,
                        "months_list": months_list,
                        "year_range": year_range,
                        "day_range": day_range,
                        "error": _(err),
                    },
                )
            data = image.read()
            info.avatar.save(image.name, ContentFile(data), save=False)

        info.save()

        if info.first_name and info.last_name and info.email and info.birth_date:
            return redirect("home")

        return render(
            request,
            "base/profile_onboarding.html",
            {
                "info": info,
                "syndrome_choices": SYNDROME_CHOICES,
                "months_list": months_list,
                "year_range": year_range,
                "day_range": day_range,
                "error": _("Please fill in the required fields."),
            },
        )

    return render(
        request,
        "base/profile_onboarding.html",
        {
            "info": info,
            "syndrome_choices": SYNDROME_CHOICES,
            "months_list": months_list,
            "year_range": year_range,
            "day_range": day_range,
        },
    )
