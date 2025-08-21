from .utils.logging import get_app_logger
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
