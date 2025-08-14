import calendar
from datetime import date, datetime
from io import BytesIO

from django.shortcuts import get_object_or_404, render
from django.http import JsonResponse
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.utils.translation import gettext_lazy as _
from django.core.files.base import ContentFile

from PIL import Image, UnidentifiedImageError

from ..models import AdditionalUserInfo

User = get_user_model()

SYNDROME_CHOICES = [
    ("s1", _("Syndrome 1")),
    ("s2", _("Syndrome 2")),
    ("s3", _("Syndrome 3")),
    ("s4", _("Syndrome 4")),
    ("s5", _("Syndrome 5")),
    ("s6", _("Syndrome 6")),
]

# --- Avatar upload constraints
MAX_AVATAR_SIZE_BYTES = 10 * 1024 * 1024
MAX_AVATAR_DIMENSION = 10_000
ALLOWED_IMAGE_FORMATS = {"JPEG", "PNG", "WEBP", "MPO"}


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

        info.syndromes = request.POST.getlist("syndromes")

        image = request.FILES.get("avatar")
        if image:
            if image.size and image.size > MAX_AVATAR_SIZE_BYTES:
                return JsonResponse({"success": False, "error": _("File is too large (max 10MB).")})

            try:
                data = image.read()
                img = Image.open(BytesIO(data))
                img.verify()
                img = Image.open(BytesIO(data))
            except UnidentifiedImageError:
                return JsonResponse({"success": False, "error": _("Unsupported image format.")})
            except Exception:
                return JsonResponse({"success": False, "error": _("Error while processing the image.")})

            if img.width > MAX_AVATAR_DIMENSION or img.height > MAX_AVATAR_DIMENSION:
                return JsonResponse(
                    {
                        "success": False,
                        "error": _("Image is too large (max 10,000 × 10,000 px)."),
                    }
                )

            if (img.format or "").upper() not in ALLOWED_IMAGE_FORMATS:
                return JsonResponse(
                    {
                        "success": False,
                        "error": _("Image format %(fmt)s is not supported.") % {"fmt": img.format},
                    }
                )

            info.avatar.save(image.name, ContentFile(data), save=False)

        info.save()
        return JsonResponse({"success": True})

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
