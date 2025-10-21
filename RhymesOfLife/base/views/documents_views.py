from datetime import datetime
import os
from urllib.parse import urlsplit, urlunsplit

from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt, csrf_protect
from django.views.decorators.cache import never_cache
from django.utils.translation import gettext_lazy as _
from django.db import transaction
from django.core.paginator import Paginator

from ..models import MedicalExam, MedicalDocument, Recommendation
from ..utils.logging import get_app_logger, get_uploads_logger
from ..utils.files import validate_mixed_upload

log = get_app_logger(__name__)
uplog = get_uploads_logger()

ALLOWED_EXTENSIONS = {".pdf", ".jpg", ".jpeg", ".png"}
ALLOWED_MIME_TYPES = {"application/pdf", "image/jpeg", "image/png"}
MAX_FILE_SIZE_BYTES = 20 * 1024 * 1024
MAX_IMAGE_DIMENSION = 10_000
EXTERNAL_LINK_MAX_LENGTH = 1000
EXTERNAL_LINKS_PER_REQUEST_LIMIT = 20


def _parse_date_yyyy_mm_dd(value: str):
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except (TypeError, ValueError):
        return None


def _json_error(message: str, status: int = 400):
    return JsonResponse({"status": "error", "message": message}, status=status)


def _normalize_external_url(raw: str | None) -> str | None:
    if not raw:
        return None
    raw = raw.strip()
    if len(raw) > EXTERNAL_LINK_MAX_LENGTH:
        return None
    if "://" not in raw:
        raw = "https://" + raw
    parts = urlsplit(raw)
    if parts.scheme not in {"http", "https"}:
        return None
    if not parts.netloc:
        return None
    return urlunsplit((parts.scheme, parts.netloc, parts.path or "/", parts.query, ""))


def _create_documents_for_exam(exam, files):
    for f in files:
        ok, msg = validate_mixed_upload(
            f,
            allowed_exts=ALLOWED_EXTENSIONS,
            allowed_mimes=ALLOWED_MIME_TYPES,
            max_size_bytes=MAX_FILE_SIZE_BYTES,
            max_image_side_px=MAX_IMAGE_DIMENSION,
        )
        if not ok:
            uplog.warning(
                "Upload validation failed: user_id=%s exam_id=%s filename=%s reason=%s",
                exam.user_info.user.id, exam.id, getattr(f, "name", ""), msg
            )
            raise ValueError(msg)
    for f in files:
        obj = MedicalDocument.objects.create(exam=exam, file=f)
        uplog.info(
            "Uploaded file: user_id=%s exam_id=%s doc_id=%s name=%s size=%s",
            exam.user_info.user.id, exam.id, obj.id, getattr(f, "name", ""), getattr(f, "size", None)
        )


def _create_external_link_document(exam, url: str):
    obj = MedicalDocument.objects.create(exam=exam, external_url=url)
    uplog.info(
        "External link attached: user_id=%s exam_id=%s doc_id=%s url=%s",
        exam.user_info.user.id, exam.id, obj.id, url
    )


def _create_external_links_for_exam(exam, urls: list[str]):
    clean = []
    seen = set()
    for u in urls[:EXTERNAL_LINKS_PER_REQUEST_LIMIT]:
        norm = _normalize_external_url(u)
        if norm and norm not in seen:
            clean.append(norm)
            seen.add(norm)
    if not clean and urls:
        raise ValueError(_("Invalid link(s)"))
    for url in clean:
        _create_external_link_document(exam, url)


@login_required
@require_http_methods(["GET", "POST"])
@csrf_protect
@never_cache
def my_documents_view(request):
    user_info = request.user.additional_info
    if request.method == "POST":
        files = request.FILES.getlist("files")
        external_url_single = _normalize_external_url(request.POST.get("external_url"))
        external_urls_multi = request.POST.getlist("external_urls[]")
        external_urls = []
        if external_url_single:
            external_urls.append(external_url_single)
        if external_urls_multi:
            external_urls.extend([u for u in external_urls_multi if u and u.strip()])
        description = request.POST.get("description", "") or ""
        exam_date = _parse_date_yyyy_mm_dd(request.POST.get("exam_date"))
        if not exam_date:
            return _json_error(_("Invalid date format"))
        if not files and not external_urls:
            return _json_error(_("No files selected. You can also add an external link."))
        try:
            with transaction.atomic():
                exam = MedicalExam.objects.create(
                    user_info=user_info,
                    exam_date=exam_date,
                    description=description,
                )
                if files:
                    _create_documents_for_exam(exam, files)
                if external_urls:
                    _create_external_links_for_exam(exam, external_urls)
        except ValueError as ve:
            log.warning("Create exam failed (validation): user_id=%s reason=%s", request.user.id, ve)
            return _json_error(str(ve))
        except Exception:
            log.exception("Create exam failed: user_id=%s", request.user.id)
            return _json_error(_("Failed to upload documents. Please try again."), status=500)
        log.info("Exam created: exam_id=%s user_id=%s date=%s", exam.id, request.user.id, exam_date)
        return JsonResponse({"status": "ok"})
    exams = user_info.medical_exams.prefetch_related("documents")
    return render(request, "base/my_documents.html", {"exams": exams})


@login_required
@require_http_methods(["GET", "POST", "DELETE"])
@csrf_protect
@never_cache
def exam_detail_api(request, exam_id):
    exam = get_object_or_404(MedicalExam, id=exam_id, user_info=request.user.additional_info)
    if request.method == "GET":
        return JsonResponse({
            "id": exam.id,
            "exam_date": exam.exam_date.strftime("%Y-%m-%d"),
            "description": exam.description,
            "documents": [
                {
                    "id": doc.id,
                    "name": os.path.basename(doc.file.name) if doc.file else doc.external_url,
                    "url": doc.file.url if doc.file else doc.external_url,
                    "is_link": bool(doc.external_url),
                }
                for doc in exam.documents.all()
            ],
        })
    if request.method == "POST":
        new_date = _parse_date_yyyy_mm_dd(request.POST.get("exam_date"))
        if not new_date:
            return _json_error(_("Invalid date format"))
        description = request.POST.get("description", "") or ""
        files = request.FILES.getlist("files")
        external_url_single = _normalize_external_url(request.POST.get("external_url"))
        external_urls_multi = request.POST.getlist("external_urls[]")
        external_urls = []
        if external_url_single:
            external_urls.append(external_url_single)
        if external_urls_multi:
            external_urls.extend([u for u in external_urls_multi if u and u.strip()])
        try:
            with transaction.atomic():
                exam.exam_date = new_date
                exam.description = description
                exam.save(update_fields=["exam_date", "description"])
                if files:
                    _create_documents_for_exam(exam, files)
                if external_urls:
                    _create_external_links_for_exam(exam, external_urls)
        except ValueError as ve:
            log.warning("Update exam failed (validation): user_id=%s exam_id=%s reason=%s", request.user.id, exam.id, ve)
            return _json_error(str(ve))
        except Exception:
            log.exception("Update exam failed: user_id=%s exam_id=%s", request.user.id, exam.id)
            return _json_error(_("Failed to update the exam."), status=500)
        log.info("Exam updated: exam_id=%s user_id=%s", exam.id, request.user.id)
        return JsonResponse({"status": "ok"})
    exam.delete()
    log.info("Exam soft-deleted: exam_id=%s user_id=%s", exam.id, request.user.id)
    return JsonResponse({"status": "ok"})


@login_required
@require_http_methods(["DELETE"])
@csrf_exempt
@never_cache
def delete_document_api(request, doc_id):
    hard = request.GET.get("hard") == "1"
    document = get_object_or_404(
        MedicalDocument.all_objects,
        id=doc_id,
        exam__user_info=request.user.additional_info,
    )
    if hard:
        if document.file:
            document.file.delete(save=False)
        document.delete(hard=True)
        uplog.info("Document hard-deleted: doc_id=%s user_id=%s", document.id, request.user.id)
    else:
        document.delete()
        uplog.info("Document soft-deleted: doc_id=%s user_id=%s", document.id, request.user.id)
    return JsonResponse({"status": "ok"})


@login_required
@require_http_methods(["GET"])
@never_cache
def recommendations_view(request):
    qs = (
        Recommendation.objects
        .filter(patient=request.user.additional_info)
        .select_related("author__user")
        .order_by("-created_at")
    )
    paginator = Paginator(qs, 10)
    page_obj = paginator.get_page(request.GET.get("page"))
    return render(
        request,
        "base/recommendations.html",
        {"page_obj": page_obj, "recommendations": page_obj.object_list},
    )
