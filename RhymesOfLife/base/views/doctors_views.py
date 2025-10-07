from functools import wraps

from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.db import transaction
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.translation import gettext_lazy as _
from django.views.decorators.http import require_http_methods

from ..models import AdditionalUserInfo, Notification, Recommendation, get_syndrome_choices
from ..utils.logging import get_app_logger

User = get_user_model()
PAGE_SIZE = 10
log = get_app_logger(__name__)


def staff_required(view_func):
    @wraps(view_func)
    def _wrapped(request, *args, **kwargs):
        if not request.user.is_staff:
            messages.error(request, _("You don't have permission to view this page."))
            log.warning("Staff-required rejected: user_id=%s path=%s", getattr(request.user, "id", None), request.path)
            return redirect("home")
        return view_func(request, *args, **kwargs)
    return _wrapped


@login_required
@staff_required
@require_http_methods(["GET"])
def patients_list_view(request):
    query = (request.GET.get("q") or "").strip()
    patients_qs = AdditionalUserInfo.objects.select_related("user")
    if query:
        patients_qs = patients_qs.filter(Q(first_name__icontains=query) | Q(last_name__icontains=query))
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
            "patients": page_obj.object_list,
            "page_obj": page_obj,
            "query": query,
            "syndrome_choices": get_syndrome_choices(),  # evaluated at request time
        },
    )


@login_required
@staff_required
@require_http_methods(["GET", "POST"])
def patient_exams_view(request, user_id: int):
    patient_user = get_object_or_404(User, id=user_id)
    patient_info = patient_user.additional_info
    exams_qs = patient_info.medical_exams.prefetch_related("documents")

    if request.method == "POST":
        content = (request.POST.get("content") or "").strip()
        if not content:
            messages.error(request, _("Recommendation cannot be empty."))
            return redirect("patient_exams", user_id=user_id)

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
                message=_("Doctor %(docname)s wrote: %(text)s") % {
                    "docname": request.user.get_full_name() or request.user.username,
                    "text": content,
                },
            )
        messages.success(request, _("Recommendation added and the patient has been notified."))
        return redirect("patient_exams", user_id=user_id)

    recommendations = (
        Recommendation.objects.filter(patient=patient_info)
        .select_related("author__user")
        .order_by("-created_at")
    )
    return render(
        request,
        "base/patient_exams.html",
        {"patient": patient_user, "exams": exams_qs, "recommendations": recommendations},
    )
