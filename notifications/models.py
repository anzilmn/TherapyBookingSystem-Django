from django.db import models
from django.contrib.auth.models import User


class Notification(models.Model):
    NOTIF_TYPES = (
        # Booking
        ('session_booked',       '📅 Session Booked'),
        ('session_approved',     '✅ Session Approved'),
        ('session_cancelled',    '❌ Session Cancelled'),
        ('session_completed',    '🏁 Session Completed'),
        ('session_reminder',     '⏰ Session Reminder'),
        # Payment
        ('payment_received',     '💰 Payment Received'),
        ('payment_done',         '💳 Payment Done'),
        # Chat & Messaging
        ('new_message',          '💬 New Message'),
        ('new_prescription',     '📋 New Prescription'),
        # Feedback
        ('review_received',      '⭐ Review Received'),
        # Account / Admin
        ('profile_approved',     '🎉 Profile Approved'),
        ('profile_pending',      '🕐 Profile Pending Review'),
        ('session_join_unlocked','🔓 Session Unlocked'),
        # General
        ('general',              'ℹ️ General'),
    )

    recipient = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='notifications'
    )
    notif_type = models.CharField(max_length=30, choices=NOTIF_TYPES, default='general')
    title = models.CharField(max_length=200)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    link = models.CharField(max_length=300, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"[{self.notif_type}] → {self.recipient.username}: {self.title}"

    @property
    def icon(self):
        icons = {
            'session_booked':        'bi-calendar-plus text-primary',
            'session_approved':      'bi-check-circle text-success',
            'session_cancelled':     'bi-x-circle text-danger',
            'session_completed':     'bi-flag-fill text-info',
            'session_reminder':      'bi-alarm text-warning',
            'payment_received':      'bi-cash-stack text-success',
            'payment_done':          'bi-credit-card text-success',
            'new_message':           'bi-chat-dots text-primary',
            'new_prescription':      'bi-file-earmark-medical text-teal',
            'review_received':       'bi-star-fill text-warning',
            'profile_approved':      'bi-patch-check-fill text-success',
            'profile_pending':       'bi-hourglass-split text-secondary',
            'session_join_unlocked': 'bi-unlock-fill text-success',
            'general':               'bi-info-circle text-secondary',
        }
        return icons.get(self.notif_type, 'bi-bell text-muted')

    @property
    def color_class(self):
        colors = {
            'session_booked':        'border-primary',
            'session_approved':      'border-success',
            'session_cancelled':     'border-danger',
            'session_completed':     'border-info',
            'session_reminder':      'border-warning',
            'payment_received':      'border-success',
            'payment_done':          'border-success',
            'new_message':           'border-primary',
            'new_prescription':      'border-teal',
            'review_received':       'border-warning',
            'profile_approved':      'border-success',
            'profile_pending':       'border-secondary',
            'session_join_unlocked': 'border-success',
            'general':               'border-secondary',
        }
        return colors.get(self.notif_type, 'border-light')
