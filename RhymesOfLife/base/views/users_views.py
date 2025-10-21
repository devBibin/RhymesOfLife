from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, Http404
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.utils.translation import gettext as _
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_POST, require_http_methods

from ..models import AdditionalUserInfo
from ..utils.decorators import permission_or_staff_required
from ..utils.logging import get_app_logger

import json

log = get_app_logger(__name__)
User = get_user_model()


@login_required
@permission_or_staff_required("base.moderate_posts")
@require_POST
@csrf_protect
def set_user_censorship(request, user_id: int):
    user = get_object_or_404(User, pk=user_id)
    info = getattr(user, "additional_info", None)
    if not info:
        return JsonResponse({"ok": False, "error": _("Profile not found.")}, status=404)
    enabled = (request.POST.get("enabled") or "").lower() in ("1", "true", "on", "yes")
    info.censorship_enabled = enabled
    info.save(update_fields=["censorship_enabled"])
    return JsonResponse({"ok": True, "enabled": info.censorship_enabled})


@login_required
@permission_or_staff_required("base.moderate_posts")
@require_http_methods(["POST"])
@csrf_protect
def toggle_user_ban(request, user_id: int):
    if request.user.id == user_id:
        return JsonResponse({"status": "error", "message": str(_("You cannot ban yourself."))}, status=400)

    target = get_object_or_404(User, pk=user_id)
    info = getattr(target, "additional_info", None)
    if not info:
        raise Http404

    reason = ""
    if request.content_type and "application/json" in request.content_type.lower():
        try:
            payload = json.loads(request.body.decode("utf-8") or "{}")
            reason = (payload.get("reason") or "").strip()
        except Exception:
            reason = ""
    else:
        reason = (request.POST.get("reason") or "").strip()

    if info.is_banned:
        info.unban()
        log.info("Unban: target_id=%s by=%s", target.id, request.user.id)
        return JsonResponse({
            "status": "ok",
            "is_banned": False,
            "message": str(_("User has been unbanned.")),
        })

    info.ban(by=request.user, reason=reason)
    log.info("Ban: target_id=%s by=%s", target.id, request.user.id)
    return JsonResponse({
        "status": "ok",
        "is_banned": True,
        "reason": info.banned_reason,
        "banned_at": timezone.localtime(info.banned_at).isoformat() if info.banned_at else None,
        "message": str(_("User has been banned.")),
    })
