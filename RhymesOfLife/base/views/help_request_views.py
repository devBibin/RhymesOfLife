from django.shortcuts import render, redirect
from django.urls import reverse
from django.contrib import messages
from django.utils.translation import gettext as _
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from django.core.paginator import Paginator
from django.views.decorators.http import require_http_methods
from django.http import JsonResponse, HttpResponseBadRequest
from django.db.models import Q
from django.utils import timezone
from django.template.loader import render_to_string
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_protect

import re

from ..models import HelpRequest
from ..utils.decorators import permission_or_staff_required

TG_RE = re.compile(r"^@?[A-Za-z0-9_]{5,32}$")
PER_PAGE = 10


def _prefill_contact(user):
    data = {"username": "", "email": "", "telegram": "", "has_tg": False}
    if not user.is_authenticated:
        return data
    info = getattr(user, "additional_info", None)
    data["username"] = (getattr(user, "username", "") or "").strip()
    data["email"] = ((getattr(info, "email", None) or getattr(user, "email", "") or "")).strip()
    if info and getattr(info, "telegram_account", None):
        tg = (info.telegram_account.username or "").strip()
        if tg:
            data["has_tg"] = True
            data["telegram"] = tg if tg.startswith("@") else f"@{tg}"
    return data


@login_required
@require_http_methods(["GET", "POST"])
def help_request_view(request):
    pre = _prefill_contact(request.user)
    context = {
        "fund_url": "https://bfastra.ru/ritmy_zhiznei",
        "values": {"username": pre["username"], "email": pre["email"], "telegram": pre["telegram"], "message": ""},
        "has_tg": pre["has_tg"],
        "errors": {},
    }

    if request.method == "POST":
        username = pre["username"]
        email = (request.POST.get("email") or pre["email"]).strip()
        telegram = pre["telegram"] if pre["has_tg"] else (request.POST.get("telegram") or "").strip()
        message = (request.POST.get("message") or "").strip()

        context["values"] = {"username": username, "email": email, "telegram": telegram, "message": message}
        errors = {}

        if not message:
            errors["message"] = _("This field is required.")

        if email:
            try:
                validate_email(email)
            except ValidationError:
                errors["email"] = _("Enter a valid email address.")

        if not pre["has_tg"] and telegram:
            handle = telegram[1:] if telegram.startswith("@") else telegram
            if not TG_RE.match(telegram) and not TG_RE.match(handle):
                errors["telegram"] = _("Enter a valid Telegram username (e.g. @john_doe).")

        if errors:
            context["errors"] = errors
        else:
            HelpRequest.objects.create(
                name=username or "",
                email=email,
                telegram=telegram,
                message=message,
            )
            messages.success(request, _("Your request has been sent. We will contact you soon."))
            return redirect(reverse("help_request"))

    return render(request, "base/help_request.html", context)


def _filter_requests(status, q):
    qs = HelpRequest.objects.all()
    s = (status or "open").lower()
    if s == "open":
        qs = qs.filter(is_processed=False)
    elif s == "processed":
        qs = qs.filter(is_processed=True)
    if q:
        qs = qs.filter(
            Q(name__icontains=q)
            | Q(email__icontains=q)
            | Q(telegram__icontains=q)
            | Q(message__icontains=q)
        )
    return qs


@login_required
@permission_or_staff_required("base.view_help_requests")
@require_http_methods(["GET"])
def staff_help_requests_page(request):
    return render(request, "base/staff_help_requests.html")


@login_required
@permission_or_staff_required("base.view_help_requests")
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


@login_required
@permission_or_staff_required("base.process_help_requests")
@require_http_methods(["POST"])
@csrf_protect
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
