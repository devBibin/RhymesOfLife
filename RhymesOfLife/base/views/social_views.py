from __future__ import annotations

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render
from django.utils.translation import gettext_lazy as _
from django.views.decorators.http import require_http_methods, require_POST

from django.contrib.auth import get_user_model

from ..models import AdditionalUserInfo, Notification
from ..utils.logging import get_app_logger

User = get_user_model()
log = get_app_logger(__name__)


@login_required
@require_POST
def follow_view(request, user_id: int):
    me: AdditionalUserInfo = request.user.additional_info
    target: AdditionalUserInfo = get_object_or_404(AdditionalUserInfo, user_id=user_id)

    if me.id == target.id:
        return JsonResponse({"success": False, "error": _("Cannot follow yourself.")}, status=400)

    rel = me.following.filter(following=target).first()
    if rel:
        if getattr(rel, "is_active", None) is False:
            rel.is_active = True
            rel.save(update_fields=["is_active"])
    else:
        me.following.create(following=target, is_active=True)

    try:
        Notification.objects.create(
            recipient=target,
            sender=me,
            notification_type="FOLLOW",
            message=_("%(username)s has followed you.") % {"username": me.user.username},
        )
    except Exception:
        log.exception("Failed to create follow notification: follower=%s target=%s", me.user_id, target.user_id)

    log.info("Follow OK: follower_user_id=%s following_user_id=%s", me.user_id, target.user_id)
    return JsonResponse({"success": True, "following": True, "user_id": user_id})


@login_required
@require_POST
def unfollow_view(request, user_id: int):
    me: AdditionalUserInfo = request.user.additional_info
    target: AdditionalUserInfo = get_object_or_404(AdditionalUserInfo, user_id=user_id)

    if me.id == target.id:
        return JsonResponse({"success": False, "error": _("Cannot unfollow yourself.")}, status=400)

    rel = me.following.filter(following=target).first()
    if not rel:
        log.info("Unfollow noop: no relation. follower=%s following=%s", me.user_id, target.user_id)
        return JsonResponse({"success": True, "following": False, "user_id": user_id})

    if hasattr(rel, "is_active"):
        if rel.is_active:
            rel.is_active = False
            rel.save(update_fields=["is_active"])
    else:
        rel.delete()

    log.info("Unfollow OK: follower_user_id=%s following_user_id=%s", me.user_id, target.user_id)
    return JsonResponse({"success": True, "following": False, "user_id": user_id})


@login_required
@require_http_methods(["GET"])
def notifications_view(request):
    user_info = request.user.additional_info
    qs = user_info.notifications.select_related("sender__user").order_by("-created_at")
    updated = qs.filter(is_read=False).update(is_read=True)
    if updated:
        log.info("Notifications marked read: user_id=%s count=%s", request.user.id, updated)
    return render(request, "base/notifications.html", {"notifications": qs})
