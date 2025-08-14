from django.shortcuts import get_object_or_404, render
from django.http import JsonResponse
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.utils.translation import gettext_lazy as _

from ..models import Notification

User = get_user_model()


@login_required
@require_http_methods(["POST"])
def follow_view(request, user_id):
    current = request.user.additional_info
    target = get_object_or_404(User, id=user_id).additional_info
    if current == target:
        return JsonResponse({"success": False, "error": _("Cannot follow yourself.")})
    current.follow(target)
    Notification.objects.create(
        recipient=target,
        sender=current,
        notification_type="FOLLOW",
        message=_("%(username)s has followed you.") % {"username": current.user.username},
    )
    return JsonResponse({"success": True})


@login_required
@require_http_methods(["POST"])
def unfollow_view(request, user_id):
    target = get_object_or_404(User, id=user_id).additional_info
    request.user.additional_info.unfollow(target)
    return JsonResponse({"success": True})


@login_required
@require_http_methods(["GET"])
def notifications_view(request):
    user_info = request.user.additional_info
    qs = user_info.notifications.select_related("sender__user").order_by("-created_at")
    qs.filter(is_read=False).update(is_read=True)
    return render(request, "base/notifications.html", {"notifications": qs})
