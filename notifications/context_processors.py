from .models import UserNotification

def notifications_context(request):
    if request.user.is_authenticated:
        unread_count = UserNotification.objects.filter(user=request.user, is_read=False).count()
        return {'unread_notifications_count': unread_count}
    return {'unread_notifications_count': 0}
