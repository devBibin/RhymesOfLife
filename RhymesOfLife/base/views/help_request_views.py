from django.shortcuts import render, redirect
from django.urls import reverse
from django.contrib import messages
from django.utils.translation import gettext as _
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from ..models import HelpRequest
from django.core.paginator import Paginator
from django.views.decorators.http import require_http_methods
from django.http import JsonResponse, HttpResponseBadRequest
from django.db.models import Q
from ..utils.decorators import staff_required
from django.utils import timezone
from django.template.loader import render_to_string


def _prefill_contact(user):
    if not user.is_authenticated:
        return "", ""
    info = getattr(user, "additional_info", None)

    def full_name(first, last):
        first = (first or "").strip()
        last = (last or "").strip()
        return (first + " " + last).strip()

    name = ""
    email = ""
    if info:
        name = full_name(info.first_name, info.last_name)
        email = (info.email or "").strip()
    if not name:
        name = full_name(getattr(user, "first_name", ""), getattr(user, "last_name", ""))
    if not name:
        name = (getattr(user, "username", "") or "").strip()
    if not email:
        email = (getattr(user, "email", "") or "").strip()
    return name, email


def help_request_view(request):
    pre_name, pre_email = _prefill_contact(request.user)
    context = {
        "fund_url": "https://bfastra.ru/ritmy_zhiznei",
        "values": {"name": pre_name, "email": pre_email, "message": ""},
        "errors": {},
    }

    if request.method == "POST":
        name = (request.POST.get("name") or pre_name).strip()
        email = (request.POST.get("email") or pre_email).strip()
        message = (request.POST.get("message") or "").strip()

        context["values"] = {"name": name, "email": email, "message": message}
        errors = {}

        if not message:
            errors["message"] = _("This field is required.")

        if email:
            try:
                validate_email(email)
            except ValidationError:
                errors["email"] = _("Enter a valid email address.")

        if errors:
            context["errors"] = errors
        else:
            HelpRequest.objects.create(name=name, email=email, message=message)
            messages.success(request, _("Your request has been sent. We will contact you soon."))
            return redirect(reverse("help_request"))

    return render(request, "base/help_request.html", context)


PER_PAGE = 10


def _filter_requests(status, q):
    qs = HelpRequest.objects.all()
    s = (status or "open").lower()
    if s == "open":
        qs = qs.filter(is_processed=False)
    elif s == "processed":
        qs = qs.filter(is_processed=True)
    if q:
        qs = qs.filter(Q(name__icontains=q) | Q(email__icontains=q) | Q(message__icontains=q))
    return qs


@staff_required
@require_http_methods(["GET"])
def staff_help_requests_page(request):
    return render(request, "base/staff_help_requests.html")


@staff_required
@require_http_methods(["GET"])
def staff_help_requests_data(request):
    status = (request.GET.get("status") or "open").lower()
    q = (request.GET.get("q") or "").strip()
    page = int(request.GET.get("page") or 1)

    qs = _filter_requests(status, q)
    paginator = Paginator(qs, PER_PAGE)
    page_obj = paginator.get_page(page)

    rows_html = render_to_string(
        "base/includes/staff_help_requests_rows.html",
        {"page_obj": page_obj},
        request=request,
    )
    pager_html = render_to_string(
        "base/includes/staff_help_requests_pager.html",
        {"page_obj": page_obj, "status": status, "q": q},
        request=request,
    )
    return JsonResponse({"ok": True, "rows": rows_html, "pager": pager_html})


@staff_required
@require_http_methods(["POST"])
def staff_help_requests_api(request):
    try:
        req_id = int(request.POST.get("id"))
        action = (request.POST.get("action") or "").lower()
    except Exception:
        return HttpResponseBadRequest(_("Invalid request."))

    try:
        item = HelpRequest.objects.get(pk=req_id)
    except HelpRequest.DoesNotExist:
        return HttpResponseBadRequest(_("Item not found."))

    if action == "process":
        item.is_processed = True
        item.processed_at = timezone.now()
        item.processed_by = request.user
        item.save(update_fields=["is_processed", "processed_at", "processed_by"])
    elif action == "undo":
        item.is_processed = False
        item.processed_at = None
        item.processed_by = None
        item.save(update_fields=["is_processed", "processed_at", "processed_by"])
    else:
        return HttpResponseBadRequest(_("Invalid action."))

    return JsonResponse({"ok": True})
