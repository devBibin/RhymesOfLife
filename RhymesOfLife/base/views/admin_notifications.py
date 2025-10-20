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

        n = Notification.objects.create(
            recipient=recipient,
            sender=sender_info,
            notification_type=ntype,
            title=title,
            message=message,
            url=url,
            payload={},
            source=source,
            scope=Notification.Scope.PERSONAL,
        )
        return JsonResponse({"status": "ok", "id": n.id})

    recipients = AdditionalUserInfo.objects.select_related("user")
    items = [
        Notification(
            recipient=r,
            sender=sender_info,
            notification_type=ntype,
            title=title,
            message=message,
            url=url,
            payload={},
            source=source,
            scope=Notification.Scope.BROADCAST,
        )
        for r in recipients
    ]
    Notification.objects.bulk_create(items, batch_size=1000)
    return JsonResponse({"status": "ok", "sent": len(items)})


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
