from datetime import datetime
import os

from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.utils.translation import gettext_lazy as _
from django.db import transaction

from ..models import MedicalExam, MedicalDocument, ExamComment
from ..utils.logging import get_app_logger, get_uploads_logger
from ..utils.files import validate_mixed_upload

log = get_app_logger(__name__)
uplog = get_uploads_logger()

ALLOWED_EXTENSIONS = {".pdf", ".jpg", ".jpeg", ".png"}
ALLOWED_MIME_TYPES = {"application/pdf", "image/jpeg", "image/png"}
MAX_FILE_SIZE_BYTES = 20 * 1024 * 1024
MAX_IMAGE_DIMENSION = 10_000


def _parse_date_yyyy_mm_dd(value: str):
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except (TypeError, ValueError):
        return None


def _json_error(message: str, status: int = 400):
    return JsonResponse({"status": "error", "message": message}, status=status)


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


@login_required
@require_http_methods(["GET", "POST"])
def my_documents_view(request):
    user_info = request.user.additional_info
    if request.method == "POST":
        files = request.FILES.getlist("files")
        description = request.POST.get("description", "") or ""
        exam_date = _parse_date_yyyy_mm_dd(request.POST.get("exam_date"))
        if not exam_date:
            return _json_error(_("Invalid date format"))
        if not files:
            return _json_error(_("No files selected"))
        try:
            with transaction.atomic():
                exam = MedicalExam.objects.create(
                    user_info=user_info,
                    exam_date=exam_date,
                    description=description,
                )
                _create_documents_for_exam(exam, files)
        except ValueError as ve:
            log.warning("Create exam failed (validation): user_id=%s reason=%s", request.user.id, ve)
            return _json_error(str(ve))
        except Exception:
            log.exception("Create exam failed: user_id=%s", request.user.id)
            return _json_error(_("Failed to upload documents. Please try again."), status=500)
        log.info("Exam created: exam_id=%s user_id=%s date=%s", exam.id, request.user.id, exam_date)
        return JsonResponse({"status": "ok"})

    exams = user_info.medical_exams.prefetch_related("documents", "comments__author__user")
    comments = (
        ExamComment.objects.filter(exam__in=exams)
        .select_related("exam", "author__user")
        .order_by("created_at")
    )
    return render(request, "base/my_documents.html", {"exams": exams, "comments": comments})


@login_required
@require_http_methods(["GET", "POST", "DELETE"])
def exam_detail_api(request, exam_id):
    exam = get_object_or_404(MedicalExam, id=exam_id, user_info=request.user.additional_info)

    if request.method == "GET":
        return JsonResponse({
            "id": exam.id,
            "exam_date": exam.exam_date.strftime("%Y-%m-%d"),
            "description": exam.description,
            "documents": [
                {"id": doc.id, "name": os.path.basename(doc.file.name), "url": doc.file.url}
                for doc in exam.documents.all()
            ],
        })

    if request.method == "POST":
        new_date = _parse_date_yyyy_mm_dd(request.POST.get("exam_date"))
        if not new_date:
            return _json_error(_("Invalid date format"))
        description = request.POST.get("description", "") or ""
        files = request.FILES.getlist("files")
        try:
            with transaction.atomic():
                exam.exam_date = new_date
                exam.description = description
                exam.save(update_fields=["exam_date", "description"])
                if files:
                    _create_documents_for_exam(exam, files)
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
