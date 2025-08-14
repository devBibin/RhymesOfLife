from datetime import datetime
import os
from io import BytesIO

from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.utils.translation import gettext_lazy as _
from django.db import transaction

import magic
from PIL import Image

from ..models import MedicalExam, MedicalDocument, ExamComment


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


def _validate_uploaded_file(uploaded_file):
    name = getattr(uploaded_file, "name", "file")
    ext = os.path.splitext(name)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        return False, _("Invalid extension: %(name)s") % {"name": name}
    if uploaded_file.size and uploaded_file.size > MAX_FILE_SIZE_BYTES:
        return False, _("File exceeds 20MB: %(name)s") % {"name": name}
    head = uploaded_file.read(1024)
    uploaded_file.seek(0)
    mime = magic.from_buffer(head, mime=True)
    if mime not in ALLOWED_MIME_TYPES:
        return False, _("Invalid MIME type: %(mime)s") % {"mime": mime}
    if mime.startswith("image/"):
        try:
            data = uploaded_file.read()
            uploaded_file.seek(0)
            img = Image.open(BytesIO(data))
            img.verify()
            img = Image.open(BytesIO(data))
            w, h = img.size
            if w > MAX_IMAGE_DIMENSION or h > MAX_IMAGE_DIMENSION:
                return False, _("Image is too large (max %(px)spx per side): %(name)s") % {
                    "px": MAX_IMAGE_DIMENSION, "name": name
                }
        except Exception:
            return False, _("Problem with image file: %(name)s") % {"name": name}
    return True, None


def _create_documents_for_exam(exam, files):
    for f in files:
        ok, msg = _validate_uploaded_file(f)
        if not ok:
            raise ValueError(msg)
    for f in files:
        MedicalDocument.objects.create(exam=exam, file=f)


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
            return _json_error(str(ve))
        except Exception:
            return _json_error(_("Failed to upload documents. Please try again."), status=500)

        return JsonResponse({"status": "ok"})

    exams = (
        user_info.medical_exams
        .prefetch_related("documents", "comments__author__user")
    )

    comments = (
        ExamComment.objects
        .filter(exam__in=exams)
        .select_related("exam", "author__user")
        .order_by("created_at")
    )

    return render(
        request,
        "base/my_documents.html",
        {"exams": exams, "comments": comments},
    )


@login_required
@require_http_methods(["GET", "POST", "DELETE"])
def exam_detail_api(request, exam_id):
    exam = get_object_or_404(
        MedicalExam,
        id=exam_id,
        user_info=request.user.additional_info,
    )

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
            return _json_error(str(ve))
        except Exception:
            return _json_error(_("Failed to update the exam."), status=500)

        return JsonResponse({"status": "ok"})

    exam.delete()
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
    else:
        document.delete()
    return JsonResponse({"status": "ok"})
