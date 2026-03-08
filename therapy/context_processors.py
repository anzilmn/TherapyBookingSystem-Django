from .models import Session
from chat.models import Message
from django.db.models import Q


def unread_messages(request):
    if request.user.is_authenticated:
        total = Message.objects.filter(
            session__in=Session.objects.filter(
                Q(patient=request.user) | Q(therapist=request.user)
            ),
            is_read=False
        ).exclude(sender=request.user).count()

        # Unread notifications count
        from notifications.models import Notification
        notif_count = Notification.objects.filter(
            recipient=request.user, is_read=False
        ).count()

        return {
            'total_unread': total,
            'notif_unread_count': notif_count,
        }
    return {'total_unread': 0, 'notif_unread_count': 0}
