from datetime import date, datetime
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.http import JsonResponse
from django.shortcuts import render
from django.utils.translation import gettext_lazy as _
from django.db import transaction
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.cache import never_cache
from django.views.decorators.debug import sensitive_post_parameters

from ..models import WellnessEntry, WellnessSettings
from ..utils.logging import get_app_logger

log = get_app_logger(__name__)


def _json_error(message: str, status: int = 400):
    return JsonResponse({"status": "error", "message": message}, status=status)


@login_required
@require_http_methods(["GET"])
@never_cache
def my_wellness_view(request):
    return render(request, "base/my_wellness.html")


@login_required
@require_http_methods(["GET", "POST", "DELETE"])
@csrf_protect
@never_cache
@sensitive_post_parameters("score", "note", "date")
def wellness_entries_api(request):
    user_info = request.user.additional_info
    user_tz = None
    tz_name = getattr(getattr(user_info, "wellness_settings", None), "reminder_tz", None) or ""
    if tz_name:
        try:
            user_tz = ZoneInfo(tz_name)
        except ZoneInfoNotFoundError:
            user_tz = None

    if request.method == "GET":
        try:
            days = int(request.GET.get("days", "90"))
        except ValueError:
            days = 90
        days = max(days, 1)
        qs = WellnessEntry.objects.filter(user_info=user_info).order_by("-date")[:days]
        items = [
            {"id": e.id, "date": e.date.strftime("%Y-%m-%d"), "score": e.score, "note": e.note}
            for e in reversed(list(qs))
        ]
        return JsonResponse({"status": "ok", "items": items})

    if request.method == "POST":
        score_raw = request.POST.get("score")
        note = (request.POST.get("note") or "")[:1000]
        date_str = request.POST.get("date")

        try:
            score = int(score_raw)
        except (TypeError, ValueError):
            return _json_error(_("Invalid score."))
        if score < 1 or score > 10:
            return _json_error(_("Score must be between 1 and 10."))

        if user_tz:
            d = datetime.now(tz=user_tz).date()
        else:
            d = date.today()
        if date_str:
            try:
                d = datetime.strptime(date_str, "%Y-%m-%d").date()
            except ValueError:
                return _json_error(_("Invalid date format."))

        try:
            with transaction.atomic():
                existing = WellnessEntry.all_objects.filter(user_info=user_info, date=d).first()
                if existing:
                    existing.is_deleted = False
                    existing.deleted_at = None
                    existing.score = score
                    existing.note = note
                    existing.save(update_fields=["is_deleted", "deleted_at", "score", "note"])
                    obj = existing
                else:
                    obj = WellnessEntry.objects.create(
                        user_info=user_info, date=d, score=score, note=note
                    )
        except Exception:
            log.exception("Wellness save failed: user_id=%s", request.user.id)
            return _json_error(_("Failed to save."), status=500)

        return JsonResponse({
            "status": "ok",
            "item": {"id": obj.id, "date": obj.date.strftime("%Y-%m-%d"), "score": obj.score, "note": obj.note},
        })

    entry_id = request.GET.get("id")
    if not entry_id:
        return _json_error(_("Missing id."))
    try:
        entry = WellnessEntry.objects.get(id=entry_id, user_info=user_info)
    except WellnessEntry.DoesNotExist:
        return _json_error(_("Not found."), status=404)
    entry.delete()
    return JsonResponse({"status": "ok"})


@login_required
@require_http_methods(["GET", "POST"])
@csrf_protect
@never_cache
@sensitive_post_parameters("reminder_hour", "reminder_minute", "reminder_interval")
def wellness_settings_api(request):
    user_info = request.user.additional_info
    obj, _ = WellnessSettings.objects.get_or_create(user_info=user_info)

    if request.method == "GET":
        return JsonResponse({
            "status": "ok",
            "settings": {
                "reminder_hour": obj.reminder_hour,
                "reminder_minute": obj.reminder_minute,
                "reminder_interval": obj.reminder_interval,
                "tg_notifications_enabled": obj.tg_notifications_enabled,
                "email_notifications_enabled": obj.email_notifications_enabled,
                "reminder_tz": getattr(obj, "reminder_tz", "") or "",
            }
        })

    hour = request.POST.get("reminder_hour")
    minute = request.POST.get("reminder_minute")
    interval = request.POST.get("reminder_interval")
    tg_enabled = request.POST.get("tg_notifications_enabled")
    email_enabled = request.POST.get("email_notifications_enabled")
    reminder_tz = (request.POST.get("reminder_tz") or "").strip()

    try:
        fields = []
        if hour is not None:
            obj.reminder_hour = max(0, min(23, int(hour)))
            fields.append("reminder_hour")
        if minute is not None:
            obj.reminder_minute = max(0, min(59, int(minute)))
            fields.append("reminder_minute")
        if interval is not None:
            iv = int(interval)
            if iv in (0, 1, 3, 7):
                obj.reminder_interval = iv
                fields.append("reminder_interval")
                if iv == 0:
                    obj.tg_notifications_enabled = False
                    obj.email_notifications_enabled = False
                    fields.extend(["tg_notifications_enabled", "email_notifications_enabled"])
        if tg_enabled is not None:
            obj.tg_notifications_enabled = str(tg_enabled).lower() in ("1", "true", "on", "yes")
            fields.append("tg_notifications_enabled")
        if email_enabled is not None:
            obj.email_notifications_enabled = str(email_enabled).lower() in ("1", "true", "on", "yes")
            fields.append("email_notifications_enabled")
        if obj.reminder_interval == 0:
            obj.tg_notifications_enabled = False
            obj.email_notifications_enabled = False
            fields.extend(["tg_notifications_enabled", "email_notifications_enabled"])
        if reminder_tz:
            try:
                ZoneInfo(reminder_tz)
                obj.reminder_tz = reminder_tz
                fields.append("reminder_tz")
            except ZoneInfoNotFoundError:
                pass
        if fields:
            fields = list(dict.fromkeys(fields))
            obj.save(update_fields=fields)
    except Exception:
        log.exception("Wellness settings save failed: user_id=%s", request.user.id)
        return _json_error(_("Failed to save settings."), status=500)

    return JsonResponse({"status": "ok"})
