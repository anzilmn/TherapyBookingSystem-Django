from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from .models import Notification


@login_required
def notification_list(request):
    """Full notifications page."""
    notifications = Notification.objects.filter(recipient=request.user)
    # Mark all as read when user opens the page
    notifications.filter(is_read=False).update(is_read=True)
    return render(request, 'notifications/notification_list.html', {
        'notifications': notifications,
    })


@login_required
@require_POST
def mark_read(request, notif_id):
    """Mark a single notification as read (AJAX)."""
    notif = get_object_or_404(Notification, id=notif_id, recipient=request.user)
    notif.is_read = True
    notif.save()
    return JsonResponse({'status': 'ok'})


@login_required
@require_POST
def mark_all_read(request):
    """Mark ALL notifications as read."""
    Notification.objects.filter(recipient=request.user, is_read=False).update(is_read=True)
    return JsonResponse({'status': 'ok', 'message': 'All notifications marked as read.'})


@login_required
@require_POST
def delete_notification(request, notif_id):
    """Delete a single notification."""
    notif = get_object_or_404(Notification, id=notif_id, recipient=request.user)
    notif.delete()
    return JsonResponse({'status': 'ok'})


@login_required
def unread_count(request):
    """API endpoint for live badge updates."""
    count = Notification.objects.filter(recipient=request.user, is_read=False).count()
    return JsonResponse({'count': count})
