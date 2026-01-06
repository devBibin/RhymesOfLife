from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import render
from django.views.decorators.http import require_http_methods
from django.views.decorators.cache import never_cache

from ..models import MedicalExam, MedicalDocument, Recommendation, MedicationEntry


@login_required
@require_http_methods(["GET"])
@never_cache
def my_health_view(request):
    return render(request, "base/my_health.html")


@login_required
@require_http_methods(["GET"])
@never_cache
def health_documents_partial(request):
    exams = (
        MedicalExam.objects
        .filter(user_info=request.user.additional_info)
        .only("id", "exam_date", "description", "created_at")
        .order_by("-exam_date", "-created_at")
    )
    MedicalDocument_qs = (
        MedicalDocument.objects
        .filter(exam__in=exams)
        .only("id", "external_url", "file", "uploaded_at", "exam_id")
    )
    docs_map = {}
    for d in MedicalDocument_qs:
        docs_map.setdefault(d.exam_id, []).append(d)
    return render(request, "base/partials/health_documents.html", {"exams": exams, "docs_map": docs_map})


@login_required
@require_http_methods(["GET"])
@never_cache
def health_recommendations_partial(request):
    qs = (
        Recommendation.objects
        .filter(patient=request.user.additional_info)
        .select_related("author__user")
        .only("id", "content", "created_at", "author__user__first_name", "author__user__last_name", "author__user__username")
        .order_by("-created_at")
    )
    paginator = Paginator(qs, 10)
    page_obj = paginator.get_page(request.GET.get("page"))
    return render(request, "base/partials/health_recommendations.html", {
        "page_obj": page_obj,
        "recommendations": page_obj.object_list
    })


@login_required
@require_http_methods(["GET"])
@never_cache
def health_wellness_partial(request):
    return render(request, "base/partials/health_wellness.html")


@login_required
def health_medications_partial(request):
    user_info = request.user.additional_info

    medications = (
        MedicationEntry.objects
        .filter(user_info=user_info)
        .order_by("-created_at")
    )

    return render(
        request,
        "base/partials/health_medications_partial.html",
        {"medications": medications},
    )
