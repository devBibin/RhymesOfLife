from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db import transaction
from django.db.models import Q
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from django.contrib.auth import get_user_model

from ..models import AdditionalUserInfo, MedicalExam, ExamComment, Notification

User = get_user_model()

PAGE_SIZE = 10


@login_required
@require_http_methods(["GET"])
def patients_list_view(request):
    if not request.user.is_staff:
        messages.info(request, _("You don't have permission to view this page."))
        return redirect("home")

    query = (request.GET.get("q") or "").strip()

    # Use select_related to avoid N+1 on user fields
    patients_qs = AdditionalUserInfo.objects.select_related("user")

    if query:
        patients_qs = patients_qs.filter(
            Q(first_name__icontains=query) | Q(last_name__icontains=query)
        )

    paginator = Paginator(patients_qs.order_by("last_name", "first_name"), PAGE_SIZE)

    page_number = request.GET.get("page") or 1
    try:
        page_obj = paginator.page(page_number)
    except PageNotAnInteger:
        page_obj = paginator.page(1)
    except EmptyPage:
        page_obj = paginator.page(paginator.num_pages)

    return render(
        request,
        "base/patients_list.html",
        {
            "query": query,
            "page_obj": page_obj,
            "patients": page_obj.object_list,  # convenience for templates
        },
    )


@login_required
@require_http_methods(["GET", "POST"])
def patient_exams_view(request, user_id: int):
    if not request.user.is_staff:
        messages.info(request, _("You don't have permission to view this page."))
        return redirect("home")

    patient_user = get_object_or_404(User, id=user_id)
    patient_info = getattr(patient_user, "additional_info", None)
    if patient_info is None:
        # If the patient profile is missing, consider it a 404 to avoid leaking user existence.
        messages.error(request, _("Patient profile was not found."))
        return redirect("patients_list")

    exams_qs = (
        patient_info.medical_exams.prefetch_related("documents", "comments__author__user")
    )

    if request.method == "POST":
        exam_id = request.POST.get("exam_id")
        content = (request.POST.get("content") or "").strip()

        if not exam_id:
            messages.error(request, _("Exam identifier is required."))
            return redirect("patient_exams", user_id=user_id)

        if not content:
            messages.error(request, _("Recommendation cannot be empty."))
            return redirect("patient_exams", user_id=user_id)

        exam = get_object_or_404(MedicalExam, id=exam_id, user_info=patient_info)

        # Author must have a profile to appear as the comment author.
        author_info = getattr(request.user, "additional_info", None)
        if author_info is None:
            messages.error(request, _("Your profile is incomplete. Please contact an administrator."))
            return redirect("patient_exams", user_id=user_id)

        with transaction.atomic():
            ExamComment.objects.create(
                exam=exam,
                author=author_info,
                content=content,
            )
            Notification.objects.create(
                recipient=exam.user_info,
                sender=author_info,
                notification_type="EXAM_COMMENT",
                message=_(
                    "Doctor %(docname)s left a recommendation for the exam on %(date)s."
                )
                % {
                    "docname": request.user.get_full_name() or request.user.username,
                    "date": exam.exam_date.strftime("%d.%m.%Y"),
                },
            )

        messages.success(request, _("Recommendation added and the patient has been notified."))
        return redirect("patient_exams", user_id=user_id)

    return render(
        request,
        "base/patient_exams.html",
        {
            "patient": patient_user,
            "exams": exams_qs,
        },
    )
