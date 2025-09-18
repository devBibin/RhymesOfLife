from .utils.logging import get_app_logger
from typing import Dict, Any
from django.contrib.auth.models import AnonymousUser

log = get_app_logger(__name__)


def notifications(request):
    if not request.user.is_authenticated or request.user.is_superuser:
        return {}
    user_info = request.user.additional_info
    unread_count = user_info.notifications.filter(is_read=False).count()
    latest = user_info.notifications.order_by('-created_at')[:5]
    log.debug("Context notifications: user_id=%s unread=%s", request.user.id, unread_count)
    return {
        'unread_notifications_count': unread_count,
        'latest_notifications': latest,
    }


def following_user_ids(request) -> Dict[str, Any]:
    user = getattr(request, "user", None)
    if not user or isinstance(user, AnonymousUser) or not user.is_authenticated:
        return {}
    me = getattr(user, "additional_info", None)
    if not me:
        return {}
    ids = list(me.following.filter(is_active=True).values_list("following__user_id", flat=True))
    return {"following_user_ids": ids}
