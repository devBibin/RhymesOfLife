from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext as _
from django.views.decorators.http import require_POST, require_http_methods

from ..models import AdditionalUserInfo, PatientAccessRequest
from ..utils.notify import send_notification_multichannel
from ..utils.access import is_external_doctor

User = get_user_model()


def _can_request_access(user) -> bool:
    return (
        user.is_authenticated
        and not user.is_superuser
        and (
            is_external_doctor(user)
            or (
                not user.is_staff
                and user.has_perm("base.view_patient_list")
                and not user.has_perm("base.view_patient_exams")
            )
        )
    )


@login_required
@require_POST
def request_access_view(request, user_id: int):
    if not _can_request_access(request.user):
        messages.error(request, _("You don't have permission to request access."))
        return redirect("patients_list")

    doctor_info = get_object_or_404(AdditionalUserInfo, user=request.user)
    patient_user = get_object_or_404(
        User,
        id=user_id,
        is_staff=False,
        is_superuser=False,
    )
    patient_info = getattr(patient_user, "additional_info", None)
    if not patient_info or patient_info.user_id == request.user.id:
        messages.error(request, _("Invalid patient."))
        return redirect("patients_list")

    req, created = PatientAccessRequest.objects.get_or_create(
        doctor=doctor_info,
        patient=patient_info,
        defaults={"status": PatientAccessRequest.Status.PENDING},
    )
    if not created:
        if req.status == PatientAccessRequest.Status.APPROVED:
            messages.info(request, _("Access is already granted."))
            return redirect("patients_list")
        if req.status == PatientAccessRequest.Status.PENDING:
            messages.info(request, _("Access request is already pending."))
            return redirect("patients_list")
        req.status = PatientAccessRequest.Status.PENDING
        req.decided_at = None
        req.save(update_fields=["status", "decided_at", "updated_at"])

    url = request.build_absolute_uri(reverse("access_requests"))
    send_notification_multichannel(
        recipient=patient_info,
        sender=doctor_info,
        notification_type="ACCESS_REQUEST",
        title=_("Access request"),
        message=_("%(doctor)s requests access to your health data.")
        % {"doctor": request.user.get_full_name() or request.user.username},
        url=url,
        button_text=_("Review"),
    )
    messages.success(request, _("Access request sent."))
    return redirect("patients_list")


@login_required
@require_http_methods(["GET"])
def access_requests_view(request):
    user_info = get_object_or_404(AdditionalUserInfo, user=request.user)
    requests_qs = (
        PatientAccessRequest.objects
        .select_related("doctor__user")
        .filter(patient=user_info)
        .order_by("-created_at")
    )
    return render(
        request,
        "base/access_requests.html",
        {"requests": requests_qs},
    )


@login_required
@require_POST
def decide_access_request_view(request, request_id: int):
    user_info = get_object_or_404(AdditionalUserInfo, user=request.user)
    action = request.POST.get("action")
    req = get_object_or_404(PatientAccessRequest, id=request_id, patient=user_info)

    if action not in ("approve", "deny"):
        messages.error(request, _("Invalid action."))
        return redirect("access_requests")

    if action == "approve":
        req.status = PatientAccessRequest.Status.APPROVED
        message = _(
            "Your access request was approved. You can now view the patient's exams and medical documents."
        )
        notif_type = "ACCESS_GRANTED"
    else:
        req.status = PatientAccessRequest.Status.DENIED
        message = _(
            "Your access request was denied. You don't have access to the patient's exams and medical documents."
        )
        notif_type = "ACCESS_DENIED"

    req.decided_at = timezone.now()
    req.save(update_fields=["status", "decided_at", "updated_at"])

    patient_name = request.user.get_full_name() or request.user.username
    send_notification_multichannel(
        recipient=req.doctor,
        sender=user_info,
        notification_type=notif_type,
        title=_("Access request update"),
        message=_("%(patient)s: %(message)s") % {"patient": patient_name, "message": message},
        url=request.build_absolute_uri(reverse("patients_list")),
        button_text=_("Open"),
    )

    messages.success(request, _("Request updated."))
    return redirect("access_requests")
