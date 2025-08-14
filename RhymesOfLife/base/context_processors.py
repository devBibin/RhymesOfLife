
def notifications(request):
    if not request.user.is_authenticated:
        return {}
    user_info = request.user.additional_info
    unread_count = user_info.notifications.filter(is_read=False).count()
    latest = user_info.notifications.order_by('-created_at')[:5]
    return {
        'unread_notifications_count': unread_count,
        'latest_notifications': latest,
    }
