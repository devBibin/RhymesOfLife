from django.contrib.auth.decorators import login_required
from django.http import HttpRequest, HttpResponse, JsonResponse, HttpResponseBadRequest
from django.shortcuts import get_object_or_404, render
from django.utils.translation import gettext as _
from django.views.decorators.http import require_POST

from ..models import MedicationEntry, AdditionalUserInfo

@login_required
def medications_page(request: HttpRequest) -> HttpResponse:
    user_info = get_object_or_404(AdditionalUserInfo, user=request.user)

    medications = (
        MedicationEntry.objects
        .filter(user_info=user_info)
        .order_by("-created_at")
    )

    return render(
        request,
        "base/health/medications.html",
        {
            "medications": medications,
            "page_title": _("Medications I take"),
        },
    )

@login_required
@require_POST
def add_medication(request: HttpRequest) -> JsonResponse:
    user_info = get_object_or_404(AdditionalUserInfo, user=request.user)

    description = (request.POST.get("description") or "").strip()

    if not description:
        return JsonResponse(
            {"error": _("Medication description is required.")},
            status=400,
        )

    if len(description) > 255:
        return JsonResponse(
            {"error": _("Medication description is too long.")},
            status=400,
        )

    MedicationEntry.objects.create(
        user_info=user_info,
        description=description,
    )

    return JsonResponse({"ok": True})


@login_required
@require_POST
def delete_medication(request: HttpRequest, pk: int) -> JsonResponse:
    user_info = get_object_or_404(AdditionalUserInfo, user=request.user)

    medication = get_object_or_404(
        MedicationEntry,
        pk=pk,
        user_info=user_info,
    )

    medication.delete()

    return JsonResponse({"ok": True})
