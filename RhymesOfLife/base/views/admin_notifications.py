import json
from django.http import JsonResponse, HttpResponseBadRequest
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.utils.translation import gettext_lazy as _
from django.views.decorators.http import require_http_methods
from django.db.models import Q
from ..models import AdditionalUserInfo, Notification
from ..utils.logging import get_app_logger
from ..utils.decorators import permission_or_staff_required
from ..utils.notify import send_notification_multichannel

log = get_app_logger(__name__)


@login_required
@permission_or_staff_required("base.send_notifications")
@require_http_methods(["GET"])
def admin_notify_page(request):
    return render(request, "base/admin_notify.html")


@login_required
@permission_or_staff_required("base.send_notifications")
@require_http_methods(["POST"])
def admin_notify_api(request):
    try:
        data = json.loads(request.body.decode("utf-8"))
    except Exception:
        return HttpResponseBadRequest(_("Invalid JSON"))

    scope = (data.get("scope") or "").strip()
    ntype = (data.get("notification_type") or "").strip()
    title = (data.get("title") or "").strip()
    message = (data.get("message") or "").strip()
    url = (data.get("url") or "").strip()
    button_text = (data.get("button_text") or "").strip()
    recipient_id = data.get("recipient_id")
    recipient_username = (data.get("recipient_username") or "").strip()

    if scope not in ("personal", "broadcast"):
        return HttpResponseBadRequest(_("Invalid scope"))
    if ntype not in ("ADMIN_MESSAGE", "SYSTEM_MESSAGE"):
        return HttpResponseBadRequest(_("Invalid type"))
    if not message:
        return HttpResponseBadRequest(_("Message is required"))

    sender_info = getattr(request.user, "additional_info", None)
    source = Notification.Source.ADMIN if ntype == "ADMIN_MESSAGE" else Notification.Source.SYSTEM

    if scope == "personal":
        if not recipient_id and not recipient_username:
            return HttpResponseBadRequest(_("Recipient is required for personal scope"))
        try:
            if recipient_id:
                recipient = AdditionalUserInfo.objects.select_related("user").get(pk=recipient_id)
            else:
                recipient = (AdditionalUserInfo.objects
                             .select_related("user")
                             .get(user__username__iexact=recipient_username))
        except AdditionalUserInfo.DoesNotExist:
            return HttpResponseBadRequest(_("Recipient not found"))

        res = send_notification_multichannel(
            recipient=recipient,
            sender=sender_info,
            notification_type=ntype,
            title=title,
            message=message,
            url=url,
            button_text=button_text,
            source=source,
            scope=Notification.Scope.PERSONAL,
            via_site=True,
            via_telegram=True,
            via_email=True,
        )
        return JsonResponse({"status": "ok", "id": res.get("notification_id")})

    sent = 0
    recipients = AdditionalUserInfo.objects.select_related("user").all()
    for r in recipients:
        send_notification_multichannel(
            recipient=r,
            sender=sender_info,
            notification_type=ntype,
            title=title,
            message=message,
            url=url,
            button_text=button_text,
            source=source,
            scope=Notification.Scope.BROADCAST,
            via_site=True,
            via_telegram=True,
            via_email=True,
        )
        sent += 1
    return JsonResponse({"status": "ok", "sent": sent})


@login_required
@permission_or_staff_required("base.send_notifications")
@require_http_methods(["GET"])
def admin_user_suggest(request):
    q = (request.GET.get("q") or "").strip()
    if not q:
        return JsonResponse({"items": []})
    qs = (AdditionalUserInfo.objects
          .select_related("user")
          .filter(Q(user__username__istartswith=q))[:10])
    items = [{"id": i.id, "username": i.user.username, "email": i.email or ""} for i in qs]
    return JsonResponse({"items": items})
