"""
therapy/views.py - Updated with full notification system, IST time-based session unlock, and validations.
"""
import hashlib
import json
from datetime import datetime, timedelta

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.db.models import Q, Sum, Avg
from django.db.models.functions import TruncDate
from django.utils import timezone

from .models import TherapistProfile, Session, Review, ContactMessage, Prescription, JournalEntry, Complaint
from accounts.models import Profile
from chat.models import Message as ChatMessage

from notifications.utils import (
    notify_session_booked,
    notify_session_approved,
    notify_session_cancelled,
    notify_session_completed,
    notify_payment_done,
    notify_prescription_added,
    notify_review_received,
)


# ── Time slot label map (start time string → display range) ───────────────────
TIME_SLOT_LABELS = {
    "09:00 AM": "9 AM – 10 AM",
    "10:00 AM": "10 AM – 11 AM",
    "11:00 AM": "11 AM – 12 PM",
    "01:00 PM": "1 PM – 2 PM",
    "02:00 PM": "2 PM – 3 PM",
    "03:00 PM": "3 PM – 4 PM",
    "04:00 PM": "4 PM – 5 PM",
    "05:00 PM": "5 PM – 6 PM",
    "07:00 PM": "7 PM – 8 PM",
}

# ── IST Time-lock helper ──────────────────────────────────────────────────────

def _is_session_joinable(session):
    """
    True only if current IST time is within the join window:
    15 minutes before session start up to 90 minutes after start.
    """
    from zoneinfo import ZoneInfo
    ist = ZoneInfo('Asia/Kolkata')
    now_ist = timezone.localtime(timezone.now())
    today_ist = now_ist.date()

    if session.date != today_ist:
        return False

    session_dt = datetime.combine(session.date, session.time_slot).replace(tzinfo=ist)
    delta_minutes = (now_ist - session_dt).total_seconds() / 60
    return -15 <= delta_minutes <= 90


def _is_chat_unlocked(session):
    """
    Chat is only unlocked during the same time window as video call.
    15 minutes before session start up to 90 minutes after start.
    """
    return _is_session_joinable(session)


def _can_finish_session(session):
    """
    Finish button unlocks only AFTER the session has ENDED.
    Each session is 1 hour, so finish unlocks at session_start + 60 minutes.
    e.g. 7 PM – 8 PM slot → finish unlocks at 8:00 PM IST.
    """
    from zoneinfo import ZoneInfo
    ist = ZoneInfo('Asia/Kolkata')
    now_ist = timezone.localtime(timezone.now())
    today_ist = now_ist.date()

    # Must be on or after the session date
    if session.date > today_ist:
        return False

    # On the same day, must be at or after session END time (start + 60 min)
    if session.date == today_ist:
        session_start = datetime.combine(session.date, session.time_slot).replace(tzinfo=ist)
        session_end = session_start + timedelta(hours=1)
        return now_ist >= session_end

    # Past dates – always allow finish
    return True


# ── 1. ROUTING ────────────────────────────────────────────────────────────────

@login_required
def dashboard_redirect(request):
    if hasattr(request.user, 'profile') and request.user.profile.role == 'therapist':
        return redirect('therapist_dashboard')
    return redirect('patient_dashboard')


def index(request):
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        email = request.POST.get('email', '').strip()
        message_content = request.POST.get('message', '').strip()
        if not name or not email or not message_content:
            messages.error(request, "All fields are required.")
            return redirect('index')
        ContactMessage.objects.create(name=name, email=email, message=message_content)
        messages.success(request, f"Thank you, {name}! Your message has been sent.")
        return redirect('index')

    return render(request, 'index.html', {
        'therapists': TherapistProfile.objects.filter(is_approved=True)[:6],
        'reviews': Review.objects.filter(rating__gte=4).order_by('-id')[:3],
        'total_patients': User.objects.filter(is_staff=False, is_superuser=False).count(),
        'total_therapists': TherapistProfile.objects.filter(is_approved=True).count(),
    })


# ── 2. THERAPIST VIEWS ────────────────────────────────────────────────────────

@login_required
def therapist_dashboard(request):
    if not hasattr(request.user, 'profile') or request.user.profile.role != 'therapist':
        return redirect('patient_dashboard')
    try:
        therapist_info = TherapistProfile.objects.get(user=request.user)
    except TherapistProfile.DoesNotExist:
        return redirect('complete_profile')

    # ── BLOCKED CHECK ──────────────────────────────────────────────────────────
    if therapist_info.is_blocked:
        return render(request, 'therapy/account_blocked.html', {
            'block_reason': therapist_info.block_reason or 'No reason provided.'
        })

    sessions = Session.objects.filter(therapist=request.user).prefetch_related('chat_messages').order_by('-created_at')
    total_earnings = sessions.filter(is_paid=True, status='completed').aggregate(Sum('amount'))['amount__sum'] or 0
    pending_payout = sessions.filter(is_paid=True, status='approved').aggregate(Sum('amount'))['amount__sum'] or 0

    for s in sessions:
        s.unread_count = s.chat_messages.filter(is_read=False).exclude(sender=request.user).count()
        s.last_message = s.chat_messages.order_by('-timestamp').first()
        s.can_join = _is_session_joinable(s) and s.is_paid and s.status == 'approved'
        s.can_chat = _is_chat_unlocked(s) and s.is_paid and s.status == 'approved'
        s.can_finish = _can_finish_session(s) and s.is_paid and s.status == 'approved'
        slot_key = s.time_slot.strftime('%I:%M %p').lstrip('0') if s.time_slot else ''
        s.time_slot_label = TIME_SLOT_LABELS.get(s.time_slot.strftime('%I:%M %p'), str(s.time_slot))

    return render(request, 'therapy/therapist_dashboard.html', {
        'info': therapist_info,
        'sessions': sessions,
        'total_earnings': total_earnings,
        'pending_payout': pending_payout,
    })


@login_required
def complete_profile(request):
    if TherapistProfile.objects.filter(user=request.user).exists():
        return redirect('therapist_dashboard')

    if request.method == 'POST':
        qualification = request.POST.get('qualification', '').strip()
        specialization = request.POST.get('specialization', '').strip()
        experience = request.POST.get('experience', '').strip()
        bio = request.POST.get('bio', '').strip()
        certificate = request.FILES.get('certificate')

        errors = []
        if not qualification: errors.append("Qualification is required.")
        if not specialization: errors.append("Specialization is required.")
        if not experience or not experience.isdigit(): errors.append("Valid experience years required.")
        if not bio or len(bio) < 30: errors.append("Bio must be at least 30 characters.")
        if not certificate: errors.append("Certificate upload is required.")

        if errors:
            for e in errors: messages.error(request, e)
            return render(request, 'therapy/complete_profile.html')

        profile_img = request.FILES.get('profile_pic')
        if profile_img:
            p = request.user.profile
            p.profile_pic = profile_img
            p.save()

        TherapistProfile.objects.create(
            user=request.user, qualification=qualification, specialization=specialization,
            experience_years=int(experience), bio=bio, certificate=certificate, is_approved=False,
        )
        messages.info(request, "Profile submitted! Awaiting admin approval.")
        return redirect('therapist_dashboard')

    return render(request, 'therapy/complete_profile.html')


@login_required
def update_session(request, session_id, action):
    session = get_object_or_404(Session, id=session_id)
    if request.user != session.therapist:
        messages.error(request, "Not authorized.")
        return redirect('dashboard_redirect')

    if action == 'approve':
        if session.status != 'pending':
            messages.error(request, "Only pending sessions can be approved.")
            return redirect('dashboard_redirect')
        session.status = 'approved'
        session.save()
        notify_session_approved(session)
        messages.success(request, "Session approved! Patient notified. ✅")

    elif action == 'cancel':
        if session.status == 'completed':
            messages.error(request, "Completed sessions cannot be cancelled.")
            return redirect('dashboard_redirect')
        session.status = 'cancelled'
        session.save()
        notify_session_cancelled(session, cancelled_by=request.user)
        messages.warning(request, "Session cancelled. Patient notified.")

    elif action == 'complete':
        if not session.is_paid:
            messages.error(request, "Session is not yet paid.")
            return redirect('dashboard_redirect')
        return redirect('add_prescription', session_id=session.id)

    return redirect('dashboard_redirect')


# ── 3. PATIENT VIEWS ──────────────────────────────────────────────────────────

@login_required
def patient_dashboard(request):
    if hasattr(request.user, 'profile') and request.user.profile.role == 'therapist':
        return redirect('therapist_dashboard')

    today = timezone.localdate()
    date_list = [today - timedelta(days=i) for i in range(6, -1, -1)]
    mood_history = (
        JournalEntry.objects.filter(patient=request.user, created_at__date__gte=date_list[0])
        .annotate(day=TruncDate('created_at')).values('day')
        .annotate(avg_mood=Avg('mood_score')).order_by('day')
    )
    mood_map = {e['day']: e['avg_mood'] for e in mood_history}
    chart_labels = [d.strftime('%a') for d in date_list]
    chart_data = [float(mood_map.get(d, 0)) for d in date_list]

    my_sessions = Session.objects.filter(patient=request.user).prefetch_related('chat_messages').order_by('-date')
    for s in my_sessions:
        s.unread_count = s.chat_messages.filter(is_read=False).exclude(sender=request.user).count()
        s.last_message = s.chat_messages.order_by('-timestamp').first()
        s.can_join = _is_session_joinable(s) and s.is_paid and s.status == 'approved'
        s.can_chat = _is_chat_unlocked(s) and s.is_paid and s.status == 'approved'
        s.time_slot_label = TIME_SLOT_LABELS.get(s.time_slot.strftime('%I:%M %p'), str(s.time_slot))

    return render(request, 'therapy/patient_dashboard.html', {
        'therapists': TherapistProfile.objects.filter(is_approved=True),
        'sessions': my_sessions,
        'chart_labels': json.dumps(chart_labels),
        'chart_data': json.dumps(chart_data),
    })


@login_required
def book_session(request, therapist_id):
    therapist_user = get_object_or_404(User, id=therapist_id)
    # Time slots as (value, display_label) tuples: "09:00 AM" -> "9 AM - 10 AM"
    time_slots = [
        ("09:00 AM", "9 AM – 10 AM"),
        ("10:00 AM", "10 AM – 11 AM"),
        ("11:00 AM", "11 AM – 12 PM"),
        ("01:00 PM", "1 PM – 2 PM"),
        ("02:00 PM", "2 PM – 3 PM"),
        ("03:00 PM", "3 PM – 4 PM"),
        ("04:00 PM", "4 PM – 5 PM"),
        ("05:00 PM", "5 PM – 6 PM"),
        ("07:00 PM", "7 PM – 8 PM"),
    ]
    session_type = request.GET.get('type', 'single')
    if session_type not in ['single', 'couple']:
        session_type = 'single'

    from zoneinfo import ZoneInfo
    import json as _json
    ist = ZoneInfo('Asia/Kolkata')
    now_ist = timezone.localtime(timezone.now())
    current_time_24 = now_ist.strftime('%H:%M')  # e.g. "13:00"
    today_str = now_ist.date().isoformat()

    ctx = {
        'therapist': therapist_user,
        'time_slots': time_slots,
        'session_type': session_type,
        'today_str': today_str,
        'current_time_24': current_time_24,
    }

    if request.user.id == therapist_user.id:
        messages.error(request, "You cannot book a session with yourself!")
        return redirect('therapist_list')

    if not TherapistProfile.objects.filter(user=therapist_user, is_approved=True).exists():
        messages.error(request, "This therapist is not approved.")
        return redirect('therapist_list')

    if request.method == 'POST':
        date_str = request.POST.get('date', '').strip()
        time_str = request.POST.get('time', '').strip()

        if not date_str:
            messages.error(request, "Please select a date."); return render(request, 'therapy/book_session.html', ctx)
        if not time_str:
            messages.error(request, "Please select a time slot."); return render(request, 'therapy/book_session.html', ctx)

        try:
            booking_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            messages.error(request, "Invalid date."); return render(request, 'therapy/book_session.html', ctx)

        if booking_date < timezone.localdate():
            messages.error(request, "Cannot book a session in the past."); return render(request, 'therapy/book_session.html', ctx)

        try:
            formatted_time = datetime.strptime(time_str, '%I:%M %p').time()
        except ValueError:
            messages.error(request, "Invalid time."); return render(request, 'therapy/book_session.html', ctx)

        # Block booking a past time slot if booking for today
        from zoneinfo import ZoneInfo
        ist = ZoneInfo('Asia/Kolkata')
        now_ist = timezone.localtime(timezone.now())
        if booking_date == now_ist.date() and formatted_time <= now_ist.time():
            messages.error(request, "This time slot has already passed. Please choose a future slot.")
            return render(request, 'therapy/book_session.html', ctx)

        if Session.objects.filter(therapist=therapist_user, date=booking_date, time_slot=formatted_time).exclude(status='cancelled').exists():
            messages.error(request, "This slot is already taken. Choose another."); return render(request, 'therapy/book_session.html', ctx)

        if Session.objects.filter(patient=request.user, date=booking_date, time_slot=formatted_time).exclude(status='cancelled').exists():
            messages.error(request, "You already have a session booked at this time."); return render(request, 'therapy/book_session.html', ctx)

        price = 5000.00 if session_type == 'couple' else 2000.00
        session = Session.objects.create(
            patient=request.user, therapist=therapist_user, date=booking_date,
            time_slot=formatted_time, status='pending', session_type=session_type, amount=price,
        )
        notify_session_booked(session)
        display_name = therapist_user.first_name or therapist_user.username
        messages.success(request, f"Request sent! Dr. {display_name} will review it. 📅")
        return redirect('patient_dashboard')

    return render(request, 'therapy/book_session.html', ctx)


@login_required
def edit_session(request, session_id):
    session = get_object_or_404(Session, id=session_id, patient=request.user)
    if session.status != 'pending':
        messages.error(request, "Only pending sessions can be rescheduled.")
        return redirect('patient_dashboard')

    time_slots = [
        ("09:00 AM", "9 AM – 10 AM"),
        ("10:00 AM", "10 AM – 11 AM"),
        ("11:00 AM", "11 AM – 12 PM"),
        ("01:00 PM", "1 PM – 2 PM"),
        ("02:00 PM", "2 PM – 3 PM"),
        ("03:00 PM", "3 PM – 4 PM"),
        ("04:00 PM", "4 PM – 5 PM"),
        ("05:00 PM", "5 PM – 6 PM"),
        ("07:00 PM", "7 PM – 8 PM"),
    ]
    from zoneinfo import ZoneInfo
    ist = ZoneInfo('Asia/Kolkata')
    now_ist = timezone.localtime(timezone.now())
    current_time_24 = now_ist.strftime('%H:%M')
    today_str = now_ist.date().isoformat()
    ctx = {'session': session, 'time_slots': time_slots, 'today_str': today_str, 'current_time_24': current_time_24}

    if request.method == 'POST':
        date_str = request.POST.get('date', '').strip()
        time_str = request.POST.get('time', '').strip()

        if not date_str or not time_str:
            messages.error(request, "Date and time are required.")
            return render(request, 'therapy/edit_session.html', ctx)
        try:
            booking_date = datetime.strptime(date_str, '%Y-%m-%d').date()
            if booking_date < timezone.localdate():
                messages.error(request, "Cannot reschedule to a past date.")
                return render(request, 'therapy/edit_session.html', ctx)
            formatted_time = datetime.strptime(time_str, '%I:%M %p').time()
        except ValueError:
            messages.error(request, "Invalid date or time.")
            return render(request, 'therapy/edit_session.html', ctx)

        if booking_date == now_ist.date() and formatted_time <= now_ist.time():
            messages.error(request, "This time slot has already passed. Please choose a future slot.")
            return render(request, 'therapy/edit_session.html', ctx)

        if Session.objects.filter(therapist=session.therapist, date=booking_date, time_slot=formatted_time).exclude(id=session.id).exclude(status='cancelled').exists():
            messages.error(request, "That slot is taken.")
            return render(request, 'therapy/edit_session.html', ctx)

        session.date = booking_date
        session.time_slot = formatted_time
        session.save()
        messages.success(request, "Session rescheduled!")
        return redirect('patient_dashboard')

    return render(request, 'therapy/edit_session.html', ctx)


@login_required
def delete_session(request, session_id):
    session = get_object_or_404(Session, id=session_id, patient=request.user)
    if session.status == 'pending':
        notify_session_cancelled(session, cancelled_by=request.user)
        session.delete()
        messages.success(request, "Appointment cancelled.")
    else:
        messages.error(request, "Only pending sessions can be cancelled.")
    return redirect('patient_dashboard')


@login_required
def give_feedback(request, session_id):
    session = get_object_or_404(Session, id=session_id, patient=request.user)
    if session.status != 'completed':
        messages.error(request, "You can only review completed sessions.")
        return redirect('patient_dashboard')
    if hasattr(session, 'review'):
        messages.info(request, "Review already submitted.")
        return redirect('patient_dashboard')

    if request.method == 'POST':
        rating = request.POST.get('rating', '').strip()
        comment = request.POST.get('comment', '').strip()
        if not rating or not rating.isdigit() or int(rating) not in range(1, 6):
            messages.error(request, "Please select a valid rating (1–5).")
            return render(request, 'therapy/give_feedback.html', {'session': session})
        if not comment or len(comment) < 10:
            messages.error(request, "Please write a review of at least 10 characters.")
            return render(request, 'therapy/give_feedback.html', {'session': session})

        Review.objects.create(session=session, rating=int(rating), comment=comment)
        notify_review_received(session)
        messages.success(request, "Thank you for your feedback! ⭐")
        return redirect('patient_dashboard')

    return render(request, 'therapy/give_feedback.html', {'session': session})


@login_required
def file_complaint(request, session_id):
    session = get_object_or_404(Session, id=session_id, patient=request.user)
    if session.status != 'completed':
        messages.error(request, "You can only file a complaint for completed sessions.")
        return redirect('patient_dashboard')
    if hasattr(session, 'complaint'):
        messages.info(request, "You have already filed a complaint for this session.")
        return redirect('patient_dashboard')

    if request.method == 'POST':
        subject = request.POST.get('subject', '').strip()
        description = request.POST.get('description', '').strip()
        if not subject:
            messages.error(request, "Please provide a subject.")
            return render(request, 'therapy/file_complaint.html', {'session': session})
        if not description or len(description) < 20:
            messages.error(request, "Please describe the issue in at least 20 characters.")
            return render(request, 'therapy/file_complaint.html', {'session': session})

        Complaint.objects.create(
            session=session,
            patient=request.user,
            therapist=session.therapist,
            subject=subject,
            description=description,
        )
        messages.success(request, "Your complaint has been submitted. Our admin team will review it. 📋")
        return redirect('patient_dashboard')

    return render(request, 'therapy/file_complaint.html', {'session': session})

@login_required
def chat_room(request, session_id):
    session = get_object_or_404(Session, id=session_id)
    if request.user not in [session.patient, session.therapist]:
        return redirect('dashboard_redirect')

    session.chat_messages.filter(is_read=False).exclude(sender=request.user).update(is_read=True)

    if request.method == 'POST':
        if request.user == session.patient and not session.is_paid:
            messages.error(request, "Please complete payment to send messages.")
            return redirect('initiate_payment', session_id=session.id)

        content = request.POST.get('content', '').strip()
        if not content:
            messages.error(request, "Message cannot be empty.")
            return redirect('chat_room', session_id=session.id)
        if len(content) > 2000:
            messages.error(request, "Message too long (max 2000 characters).")
            return redirect('chat_room', session_id=session.id)

        msg = ChatMessage.objects.create(session=session, sender=request.user, content=content)
        from notifications.utils import notify_new_message
        notify_new_message(msg)
        return redirect('chat_room', session_id=session.id)

    return render(request, 'therapy/chat_room.html', {
        'session': session,
        'chat_messages': session.chat_messages.all(),
    })


@login_required
def video_call(request, session_id):
    """Video call with IST time-lock."""
    session = get_object_or_404(Session, id=session_id)
    if request.user not in [session.patient, session.therapist]:
        return redirect('dashboard_redirect')

    if request.user == session.patient:
        if not session.is_paid or session.status != 'approved':
            messages.error(request, "Access denied. Complete payment first.")
            return redirect('patient_dashboard')
        if not _is_session_joinable(session):
            now_ist = timezone.localtime(timezone.now())
            messages.warning(
                request,
                f"🔒 Session locked. Join on {session.date.strftime('%B %d, %Y')} at "
                f"{session.time_slot.strftime('%I:%M %p')} IST. "
                f"Current IST: {now_ist.strftime('%I:%M %p')}."
            )
            return redirect('patient_dashboard')

    if request.user == session.therapist:
        if session.status != 'approved':
            messages.error(request, "Session not approved yet.")
            return redirect('therapist_dashboard')
        if not _is_session_joinable(session):
            now_ist = timezone.localtime(timezone.now())
            messages.warning(
                request,
                f"🔒 Session not in window yet. Join on {session.date.strftime('%B %d, %Y')} at "
                f"{session.time_slot.strftime('%I:%M %p')} IST. "
                f"Current IST: {now_ist.strftime('%I:%M %p')}."
            )
            return redirect('therapist_dashboard')

    raw_name = f"MindCare-Session-{session.id}-{session.date.strftime('%Y%m%d')}"
    room_name = f"SecureTherapy_{hashlib.md5(raw_name.encode()).hexdigest()[:12]}"

    return render(request, 'therapy/video_call.html', {
        'session': session,
        'room_name': room_name,
        'user_display_name': request.user.username,
    })


# ── 5. PAYMENT ────────────────────────────────────────────────────────────────

@login_required
def initiate_payment(request, session_id):
    session = get_object_or_404(Session, id=session_id, patient=request.user)
    if session.is_paid:
        messages.info(request, "Already paid.")
        return redirect('chat_room', session_id=session.id)
    if session.status != 'approved':
        messages.error(request, "Session must be approved before payment.")
        return redirect('patient_dashboard')

    price = 5000.00 if session.session_type == 'couple' else 2000.00
    session.amount = price
    session.save()
    return render(request, 'therapy/payment_gateway.html', {'session': session, 'price': price})


@login_required
def process_payment(request, session_id):
    session = get_object_or_404(Session, id=session_id, patient=request.user)
    if session.is_paid:
        return redirect('chat_room', session_id=session.id)

    if request.method == 'POST':
        method = request.POST.get('method', '').strip()
        final_amt = request.POST.get('final_amount', '').strip()

        if not method:
            messages.error(request, "Please select a payment method.")
            return redirect('initiate_payment', session_id=session.id)

        session.is_paid = True
        if final_amt:
            try: session.amount = float(final_amt)
            except ValueError: pass
        session.save()

        notify_payment_done(session)
        messages.success(request, f"Payment via {method} successful! Session unlocked. 🎉")
        return redirect('patient_dashboard')

    return redirect('patient_dashboard')


# ── 6. PUBLIC ─────────────────────────────────────────────────────────────────

def therapist_list(request):
    return render(request, 'therapy/therapist_list.html', {
        'therapists': TherapistProfile.objects.filter(is_approved=True)
    })


# ── 7. PRESCRIPTIONS ──────────────────────────────────────────────────────────

@login_required
def add_prescription(request, session_id):
    session = get_object_or_404(Session, id=session_id, therapist=request.user)
    if hasattr(session, 'prescription'):
        messages.info(request, "Prescription already exists.")
        return redirect('therapist_dashboard')

    if request.method == 'POST':
        diagnosis = request.POST.get('diagnosis', '').strip()
        advice = request.POST.get('advice', '').strip()
        medicines = request.POST.get('medicines', '').strip()

        if not diagnosis or len(diagnosis) < 5:
            messages.error(request, "Please enter a valid diagnosis (min 5 chars).")
            return render(request, 'therapy/add_prescription.html', {'session': session})
        if not advice or len(advice) < 10:
            messages.error(request, "Please provide detailed advice (min 10 chars).")
            return render(request, 'therapy/add_prescription.html', {'session': session})

        Prescription.objects.create(session=session, diagnosis=diagnosis, advice=advice, medicines=medicines)
        session.status = 'completed'
        session.save()

        notify_session_completed(session)
        notify_prescription_added(session)

        messages.success(request, "Session complete and prescription sent! ✅")
        return redirect('therapist_dashboard')

    return render(request, 'therapy/add_prescription.html', {'session': session})


@login_required
def view_prescription(request, session_id):
    session = get_object_or_404(Session, id=session_id)
    if request.user != session.patient and request.user != session.therapist:
        messages.error(request, "Access denied.")
        return redirect('dashboard_redirect')
    return render(request, 'therapy/prescription_view.html', {
        'prescription': get_object_or_404(Prescription, session=session)
    })


@login_required
def download_prescription(request, session_id):
    session = get_object_or_404(Session, id=session_id)
    if request.user != session.patient and request.user != session.therapist:
        return redirect('dashboard_redirect')
    return render(request, 'therapy/prescription_pdf.html', {
        'prescription': get_object_or_404(Prescription, session=session)
    })


# ── 8. MISC ───────────────────────────────────────────────────────────────────

def emergency_support(request):
    return render(request, 'therapy/emergency.html')


@login_required
def journal_view(request):
    entries = JournalEntry.objects.filter(patient=request.user)

    if request.method == "POST":
        content = request.POST.get('content', '').strip()
        mood = request.POST.get('mood_score', '').strip()

        if not content:
            messages.error(request, "Entry cannot be empty.")
            return render(request, 'therapy/journal.html', {'entries': entries})
        if not mood or not mood.isdigit() or int(mood) not in range(1, 6):
            messages.error(request, "Please select a valid mood (1–5).")
            return render(request, 'therapy/journal.html', {'entries': entries})
        if len(content) > 5000:
            messages.error(request, "Entry too long (max 5000 characters).")
            return render(request, 'therapy/journal.html', {'entries': entries})

        JournalEntry.objects.create(patient=request.user, content=content, mood_score=int(mood))
        messages.success(request, "Entry saved! Proud of you for checking in. 💙")
        return redirect('journal')

    return render(request, 'therapy/journal.html', {'entries': entries})


def choose_session_type(request, therapist_id):
    therapist = get_object_or_404(TherapistProfile, user_id=therapist_id)
    return render(request, 'therapy/choose_session_type.html', {'therapist': therapist})
