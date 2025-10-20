from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, render
from django.views.decorators.http import require_http_methods

from ..models import WellnessEntry
from ..utils.decorators import staff_required

User = get_user_model()


@login_required
@staff_required
@require_http_methods(["GET"])
def patient_wellness_view(request, user_id: int):
    patient_user = get_object_or_404(User, id=user_id)
    info = patient_user.additional_info
    entries = list(WellnessEntry.objects.filter(user_info=info).order_by("-date")[:365])
    entries = list(reversed(entries))
    data = [{"date": e.date.strftime("%Y-%m-%d"), "score": e.score, "note": e.note} for e in entries]
    return render(
        request,
        "base/patient_wellness.html",
        {"patient": patient_user, "entries": data},
    )
