from .models import Notification


def notify(recipient, notif_type, title, message, link=None):
    """
    Quick helper to create a notification.
    Usage: notify(user, 'session_booked', 'Session Booked', 'Your session with Dr. X is booked.', '/therapy/patient/dashboard/')
    """
    Notification.objects.create(
        recipient=recipient,
        notif_type=notif_type,
        title=title,
        message=message,
        link=link,
    )


def notify_session_booked(session):
    """Patient books a session → notify therapist."""
    notify(
        recipient=session.therapist,
        notif_type='session_booked',
        title='New Session Request',
        message=f"{session.patient.get_full_name() or session.patient.username} has booked a {session.get_session_type_display()} session on {session.date} at {session.time_slot}.",
        link='/therapy/therapist/dashboard/',
    )
    # Also notify patient for confirmation
    notify(
        recipient=session.patient,
        notif_type='session_booked',
        title='Session Booking Confirmed',
        message=f"Your {session.get_session_type_display()} session with Dr. {session.therapist.last_name or session.therapist.username} on {session.date} at {session.time_slot} is awaiting approval.",
        link='/therapy/patient/dashboard/',
    )


def notify_session_approved(session):
    """Therapist approves → notify patient."""
    notify(
        recipient=session.patient,
        notif_type='session_approved',
        title='Session Approved! 🎉',
        message=f"Your session with Dr. {session.therapist.last_name or session.therapist.username} on {session.date} at {session.time_slot} has been approved. Please complete payment to unlock the session.",
        link='/therapy/patient/dashboard/',
    )


def notify_session_cancelled(session, cancelled_by):
    """Either party cancels → notify the other."""
    other = session.therapist if cancelled_by == session.patient else session.patient
    by_name = cancelled_by.get_full_name() or cancelled_by.username
    notify(
        recipient=other,
        notif_type='session_cancelled',
        title='Session Cancelled',
        message=f"Your session on {session.date} at {session.time_slot} has been cancelled by {by_name}.",
        link='/therapy/patient/dashboard/',
    )


def notify_session_completed(session):
    """Therapist marks complete → notify patient."""
    notify(
        recipient=session.patient,
        notif_type='session_completed',
        title='Session Completed',
        message=f"Your session with Dr. {session.therapist.last_name or session.therapist.username} on {session.date} has been marked as completed. Please leave a review!",
        link='/therapy/patient/dashboard/',
    )
    notify(
        recipient=session.therapist,
        notif_type='session_completed',
        title='Session Marked Complete',
        message=f"Session with {session.patient.get_full_name() or session.patient.username} on {session.date} is now complete. Earnings updated.",
        link='/therapy/therapist/dashboard/',
    )


def notify_payment_done(session):
    """Patient pays → notify both."""
    notify(
        recipient=session.therapist,
        notif_type='payment_received',
        title='Payment Received 💰',
        message=f"{session.patient.get_full_name() or session.patient.username} paid ₹{session.amount} for the session on {session.date} at {session.time_slot}. Session is now active.",
        link='/therapy/therapist/dashboard/',
    )
    notify(
        recipient=session.patient,
        notif_type='payment_done',
        title='Payment Successful ✅',
        message=f"Your payment of ₹{session.amount} was successful! Your session with Dr. {session.therapist.last_name or session.therapist.username} is now unlocked.",
        link='/therapy/patient/dashboard/',
    )


def notify_new_message(message_obj):
    """New chat message → notify the other party."""
    session = message_obj.session
    sender = message_obj.sender
    recipient = session.therapist if sender == session.patient else session.patient
    notify(
        recipient=recipient,
        notif_type='new_message',
        title='New Message 💬',
        message=f"{sender.get_full_name() or sender.username} sent you a message.",
        link=f'/therapy/chat/{session.id}/',
    )


def notify_prescription_added(session):
    """Therapist adds prescription → notify patient."""
    notify(
        recipient=session.patient,
        notif_type='new_prescription',
        title='New Prescription Added 📋',
        message=f"Dr. {session.therapist.last_name or session.therapist.username} has added a prescription for your session on {session.date}. You can view and download it from your dashboard.",
        link='/therapy/patient/dashboard/',
    )


def notify_review_received(session):
    """Patient leaves review → notify therapist."""
    notify(
        recipient=session.therapist,
        notif_type='review_received',
        title='New Review Received ⭐',
        message=f"{session.patient.get_full_name() or session.patient.username} left a review for your session on {session.date}.",
        link='/therapy/therapist/dashboard/',
    )


def notify_profile_approved(therapist_user):
    """Admin approves therapist profile."""
    notify(
        recipient=therapist_user,
        notif_type='profile_approved',
        title='Profile Approved! 🎉',
        message="Congratulations! Your therapist profile has been approved by the admin. You can now receive session bookings.",
        link='/therapy/therapist/dashboard/',
    )


def notify_session_reminder(session):
    """30-minute before session reminder (can be called from a cron/celery task)."""
    notify(
        recipient=session.patient,
        notif_type='session_reminder',
        title='Session Starting Soon ⏰',
        message=f"Reminder: Your session with Dr. {session.therapist.last_name or session.therapist.username} starts at {session.time_slot} today. Get ready to join!",
        link='/therapy/patient/dashboard/',
    )
    notify(
        recipient=session.therapist,
        notif_type='session_reminder',
        title='Session Starting Soon ⏰',
        message=f"Reminder: Your session with {session.patient.get_full_name() or session.patient.username} starts at {session.time_slot} today.",
        link='/therapy/therapist/dashboard/',
    )
