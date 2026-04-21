from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import get_object_or_404, render, redirect
from django.utils.translation import gettext as _
from django.views.decorators.http import require_http_methods

from ..models import WellnessEntry
from ..utils.access import has_patient_access
from ..utils.logging import get_app_logger
from .doctors_views import patient_doctor_context

User = get_user_model()
log = get_app_logger(__name__)


@login_required
@require_http_methods(["GET"])
def patient_wellness_view(request, user_id: int):
    patient_user = get_object_or_404(User, id=user_id)
    patient_info = getattr(patient_user, "additional_info", None)
    if not patient_info:
        return redirect("home")
    if not has_patient_access(request.user, patient_info):
        messages.error(request, _("Access to this patient's data is not granted."))
        return redirect("patients_list")

    entries_qs = WellnessEntry.objects.filter(user_info=patient_info).order_by("-date")[:365]
    entries = list(reversed(entries_qs))
    data = [{"date": e.date.strftime("%Y-%m-%d"), "score": e.score, "note": e.note} for e in entries]

    ctx = patient_doctor_context(request, patient_user, "wellness")
    ctx.update({"entries": data})
    return render(request, "base/patient_wellness.html", ctx)
