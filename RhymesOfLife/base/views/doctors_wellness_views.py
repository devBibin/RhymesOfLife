from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, render, redirect
from django.views.decorators.http import require_http_methods

from ..models import WellnessEntry
from ..utils.decorators import permission_or_staff_required
from ..utils.logging import get_app_logger

User = get_user_model()
log = get_app_logger(__name__)


@login_required
@permission_or_staff_required("base.view_patient_exams")
@require_http_methods(["GET"])
def patient_wellness_view(request, user_id: int):
    patient_user = get_object_or_404(User, id=user_id)
    patient_info = getattr(patient_user, "additional_info", None)
    if not patient_info:
        return redirect("home")

    entries_qs = WellnessEntry.objects.filter(user_info=patient_info).order_by("-date")[:365]
    entries = list(reversed(entries_qs))
    data = [{"date": e.date.strftime("%Y-%m-%d"), "score": e.score, "note": e.note} for e in entries]

    return render(
        request,
        "base/patient_wellness.html",
        {"patient": patient_user, "entries": data},
    )
