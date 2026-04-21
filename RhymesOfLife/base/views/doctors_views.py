from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.db import transaction
from django.db.models import Q
from django.urls import reverse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.http import url_has_allowed_host_and_scheme
from django.utils.translation import gettext_lazy as _
from django.views.decorators.http import require_http_methods

from ..models import (
    AdditionalUserInfo,
    Notification,
    Recommendation,
    SYNDROME_STATUS_DOCTOR_CONFIRMED,
    SYNDROME_STATUS_DOCTOR_UNCONFIRMED,
    SYNDROME_STATUS_GENETIC_CONFIRMED,
    get_syndrome_choices,
)
from ..utils.logging import get_app_logger
from ..utils.decorators import permission_or_staff_required
from ..utils.access import get_access_status_map, has_patient_access, is_external_doctor

User = get_user_model()
PAGE_SIZE = 10
log = get_app_logger(__name__)


def _syndrome_status_rows(info, syndrome_choices):
    status_map = getattr(info, "syndrome_statuses", None) or {}
    legacy_selected = set(getattr(info, "syndromes", None) or [])
    legacy_genetic = set(getattr(info, "confirmed_syndromes", None) or [])
    rows = []

    for code, label in syndrome_choices:
        statuses = list(status_map.get(code) or [])
        if not statuses:
            if code in legacy_genetic:
                statuses = [SYNDROME_STATUS_GENETIC_CONFIRMED]
            elif code in legacy_selected:
                statuses = [SYNDROME_STATUS_DOCTOR_UNCONFIRMED]
        if statuses:
            rows.append({
                "code": code,
                "label": label,
                "statuses": statuses,
            })
    return rows


def doctor_can_recommend(user, patient_info):
    return (
        user.is_superuser
        or user.is_staff
        or user.has_perm("base.write_recommendations")
        or has_patient_access(user, patient_info)
    )


def get_patient_recommendations(patient_info):
    return (
        Recommendation.objects.filter(patient=patient_info)
        .select_related("author__user")
        .order_by("-created_at")
    )


def patient_doctor_context(request, patient_user, active_tab):
    patient_info = patient_user.additional_info
    back_url = request.GET.get("next") or reverse("patients_list")
    if not url_has_allowed_host_and_scheme(back_url, allowed_hosts={request.get_host()}):
        back_url = reverse("patients_list")
    return {
        "patient": patient_user,
        "patient_info": patient_info,
        "active_tab": active_tab,
        "back_url": back_url,
        "can_recommend": doctor_can_recommend(request.user, patient_info),
        "recommendations": get_patient_recommendations(patient_info),
    }


@login_required
@permission_or_staff_required("base.view_patient_list")
@require_http_methods(["GET"])
def patients_list_view(request):
    query = (request.GET.get("q") or "").strip()

    patients_qs = (
        AdditionalUserInfo.objects.select_related("user")
        .filter(user__is_staff=False, user__is_superuser=False)
    )

    if query:
        patients_qs = patients_qs.filter(
            Q(first_name__icontains=query) | Q(last_name__icontains=query) | Q(user__username__icontains=query)
        )

    paginator = Paginator(patients_qs.order_by("last_name", "first_name", "user__username"), PAGE_SIZE)
    page_number = request.GET.get("page") or 1
    try:
        page_obj = paginator.page(page_number)
    except PageNotAnInteger:
        page_obj = paginator.page(1)
    except EmptyPage:
        page_obj = paginator.page(paginator.num_pages)

    can_request_access = (
        request.user.is_authenticated
        and not request.user.is_superuser
        and (
            is_external_doctor(request.user)
            or (
                not request.user.is_staff
                and request.user.has_perm("base.view_patient_list")
                and not request.user.has_perm("base.view_patient_exams")
            )
        )
    )
    access_map = {}
    if can_request_access:
        doctor_info = getattr(request.user, "additional_info", None)
        patient_ids = [p.id for p in page_obj.object_list]
        access_map = get_access_status_map(doctor_info, patient_ids)
        for info in page_obj.object_list:
            info.access_status = access_map.get(info.id)

    syndrome_choices = get_syndrome_choices()
    for info in page_obj.object_list:
        info.syndrome_status_rows = _syndrome_status_rows(info, syndrome_choices)

    return render(
        request,
        "base/patients_list.html",
        {
            "patients": page_obj.object_list,
            "page_obj": page_obj,
            "query": query,
            "syndrome_choices": syndrome_choices,
            "status_doctor_confirmed": SYNDROME_STATUS_DOCTOR_CONFIRMED,
            "status_doctor_unconfirmed": SYNDROME_STATUS_DOCTOR_UNCONFIRMED,
            "status_genetic_confirmed": SYNDROME_STATUS_GENETIC_CONFIRMED,
            "can_request_access": can_request_access,
            "access_map": access_map,
        },
    )


@login_required
@require_http_methods(["GET"])
def patient_exams_view(request, user_id: int):
    patient_user = get_object_or_404(User, id=user_id)
    patient_info = patient_user.additional_info
    if not has_patient_access(request.user, patient_info):
        messages.error(request, _("Access to this patient's data is not granted."))
        return redirect("patients_list")

    exams_qs = patient_info.medical_exams.prefetch_related("documents")

    ctx = patient_doctor_context(request, patient_user, "exams")
    ctx.update({
        "exams": exams_qs,
    })
    return render(
        request,
        "base/patient_exams.html",
        ctx,
    )


@login_required
@require_http_methods(["POST"])
def add_patient_recommendation_view(request, user_id: int):
    patient_user = get_object_or_404(User, id=user_id)
    patient_info = patient_user.additional_info
    next_url = request.POST.get("next") or request.META.get("HTTP_REFERER") or reverse("patient_exams", args=[user_id])
    if not url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()}):
        next_url = reverse("patient_exams", args=[user_id])

    if not doctor_can_recommend(request.user, patient_info):
        messages.error(request, _("You don't have permission to send recommendations."))
        return redirect(next_url)

    content = (request.POST.get("content") or "").strip()
    if not content:
        messages.error(request, _("Recommendation cannot be empty."))
        return redirect(next_url)

    author_info = request.user.additional_info
    with transaction.atomic():
        Recommendation.objects.create(
            patient=patient_info,
            author=author_info,
            content=content,
        )
        Notification.objects.create(
            recipient=patient_info,
            sender=author_info,
            notification_type="RECOMMENDATION",
            message=_("Doctor %(docname)s wrote: %(text)s")
            % {
                "docname": request.user.get_full_name() or request.user.username,
                "text": content,
            },
        )
    messages.success(request, _("Recommendation added and the patient has been notified."))
    return redirect(next_url)
