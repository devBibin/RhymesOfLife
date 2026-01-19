from datetime import datetime
from django.conf import settings
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

from ..models import HelpRequest, MedicationEntry, get_syndrome_choices
from ..utils.decorators import permission_or_staff_required
from ..utils.email_sender import send_email

TG_RE = re.compile(r"^@?[A-Za-z0-9_]{5,32}$")
PER_PAGE = 10


def _prefill_contact(user):
    data = {
        "username": "",
        "email": "",
        "telegram": "",
        "has_tg": False,
        "full_name": "",
        "phone": "",
        "birth_date": "",
        "city": "",
        "syndrome": "",
        "gen": "",
        "medications": "",
    }
    if not user.is_authenticated:
        return data
    info = getattr(user, "additional_info", None)
    data["username"] = (getattr(user, "username", "") or "").strip()
    data["email"] = ((getattr(info, "email", None) or getattr(user, "email", "") or "")).strip()
    if info:
        fn = (getattr(info, "first_name", "") or "").strip()
        ln = (getattr(info, "last_name", "") or "").strip()
        if fn or ln:
            data["full_name"] = f"{fn} {ln}".strip()
        else:
            user_fn = (getattr(user, "first_name", "") or "").strip()
            user_ln = (getattr(user, "last_name", "") or "").strip()
            data["full_name"] = f"{user_fn} {user_ln}".strip()
        data["phone"] = (getattr(info, "phone", "") or "").strip()
        bd = getattr(info, "birth_date", None)
        data["birth_date"] = bd.strftime("%Y-%m-%d") if bd else ""
        codes = list(getattr(info, "confirmed_syndromes", []) or getattr(info, "syndromes", []) or [])
        if codes:
            label_map = {c: l for c, l in get_syndrome_choices()}
            data["syndrome"] = ", ".join(label_map.get(c, c) for c in codes)
        meds = MedicationEntry.objects.filter(user_info=info).order_by("-created_at").values_list("description", flat=True)
        data["medications"] = "\n".join(meds)
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
        "values": {
            "username": pre["username"],
            "email": pre["email"],
            "telegram": pre["telegram"],
            "full_name": pre["full_name"],
            "phone": pre["phone"],
            "birth_date": pre["birth_date"],
            "city": pre["city"],
            "syndrome": pre["syndrome"],
            "gen": pre["gen"],
            "medications": pre["medications"],
            "message": "",
        },
        "has_tg": pre["has_tg"],
        "errors": {},
    }

    if request.method == "POST":
        username = pre["username"]
        email = (request.POST.get("email") or pre["email"]).strip()
        telegram = pre["telegram"] if pre["has_tg"] else (request.POST.get("telegram") or "").strip()
        full_name = (request.POST.get("full_name") or pre["full_name"]).strip()
        phone = (request.POST.get("phone") or pre["phone"]).strip()
        birth_date_raw = (request.POST.get("birth_date") or pre["birth_date"]).strip()
        city = (request.POST.get("city") or pre["city"]).strip()
        syndrome = (request.POST.get("syndrome") or pre["syndrome"]).strip()
        gen = (request.POST.get("gen") or pre["gen"]).strip()
        medications = (request.POST.get("medications") or pre["medications"]).strip()
        message = (request.POST.get("message") or "").strip()

        context["values"] = {
            "username": username,
            "email": email,
            "telegram": telegram,
            "full_name": full_name,
            "phone": phone,
            "birth_date": birth_date_raw,
            "city": city,
            "syndrome": syndrome,
            "gen": gen,
            "medications": medications,
            "message": message,
        }
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

        birth_date = None
        if birth_date_raw:
            try:
                birth_date = datetime.strptime(birth_date_raw, "%Y-%m-%d").date()
            except ValueError:
                errors["birth_date"] = _("Enter a valid date.")

        if errors:
            context["errors"] = errors
        else:
            item = HelpRequest.objects.create(
                user=request.user,
                name=full_name or username or "",
                email=email,
                phone=phone,
                birth_date=birth_date,
                city=city,
                syndrome=syndrome,
                gen=gen,
                medications=medications,
                telegram=telegram,
                message=message,
            )
            _send_help_request_copy(item)
            messages.success(request, _("Your request has been sent. We will contact you soon."))
            return redirect(reverse("help_request"))

    return render(request, "base/help_request.html", context)


def _filter_requests(status, q):
    qs = HelpRequest.objects.all()
    s = (status or "open").lower()
    if s == "open":
        qs = qs.filter(status=HelpRequest.Status.OPEN)
    elif s == "in_work":
        qs = qs.filter(status=HelpRequest.Status.IN_WORK)
    elif s == "processed":
        qs = qs.filter(status=HelpRequest.Status.DONE)
    if q:
        qs = qs.filter(
            Q(name__icontains=q)
            | Q(email__icontains=q)
            | Q(telegram__icontains=q)
            | Q(phone__icontains=q)
            | Q(city__icontains=q)
            | Q(syndrome__icontains=q)
            | Q(gen__icontains=q)
            | Q(medications__icontains=q)
            | Q(message__icontains=q)
            | Q(user__username__icontains=q)
        )
    return qs


def _send_help_request_copy(item: HelpRequest) -> None:
    to_addr = "dst@bfastra.ru"
    subject = f"Help request #{item.id}"
    base_url = (getattr(settings, "BASE_URL", "") or "").rstrip("/")
    profile_url = ""
    if item.user and base_url:
        profile_url = f"{base_url}/u/{item.user.username}/"
    lines = [
        f"Name: {item.name or '-'}",
        f"Email: {item.email or '-'}",
        f"Phone: {item.phone or '-'}",
        f"Birth date: {item.birth_date or '-'}",
        f"City: {item.city or '-'}",
        f"Syndrome: {item.syndrome or '-'}",
        f"Gen: {item.gen or '-'}",
        f"Medications: {item.medications or '-'}",
        f"Telegram: {item.telegram or '-'}",
        f"Profile: {profile_url or '-'}",
        "",
        "Message:",
        item.message or "-",
    ]
    body = "\n".join(lines)
    from_email = getattr(settings, "DEFAULT_FROM_EMAIL", "no-reply@example.com")
    try:
        send_email({
            "to": to_addr,
            "subject": subject,
            "text": body,
            "from_email": from_email,
        })
    except Exception:
        pass


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

    if action == "work":
        item.status = HelpRequest.Status.IN_WORK
        item.is_processed = False
        item.processed_at = None
        item.processed_by = request.user
        item.save(update_fields=["status", "is_processed", "processed_at", "processed_by"])
    elif action == "process":
        item.status = HelpRequest.Status.DONE
        item.is_processed = True
        item.processed_at = timezone.now()
        item.processed_by = request.user
        item.save(update_fields=["status", "is_processed", "processed_at", "processed_by"])
    elif action == "undo":
        item.status = HelpRequest.Status.OPEN
        item.is_processed = False
        item.processed_at = None
        item.processed_by = None
        item.save(update_fields=["status", "is_processed", "processed_at", "processed_by"])
    else:
        return HttpResponseBadRequest(_("Invalid action."))

    return JsonResponse({"ok": True})
