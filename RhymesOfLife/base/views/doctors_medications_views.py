from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, render, redirect
from django.utils.translation import gettext as _
from django.views.decorators.http import require_http_methods

from ..models import MedicationEntry
from ..utils.access import has_patient_access

User = get_user_model()


@login_required
@require_http_methods(["GET"])
def patient_medications_view(request, user_id: int):
    patient_user = get_object_or_404(User, id=user_id)
    patient_info = getattr(patient_user, "additional_info", None)
    if not patient_info:
        return redirect("patients_list")
    if not has_patient_access(request.user, patient_info):
        messages.error(request, _("Access to this patient's data is not granted."))
        return redirect("patients_list")

    medications = (
        MedicationEntry.objects
        .filter(user_info=patient_info)
        .order_by("-created_at")
    )

    return render(
        request,
        "base/patient_medications.html",
        {
            "patient": patient_user,
            "medications": medications,
        },
    )
