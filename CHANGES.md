# Changes Made

## 1. settings.py
- `TIME_ZONE = 'Asia/Kolkata'` (IST)
- Added `notifications` to `INSTALLED_APPS`

## 2. New App: `notifications/`
- `models.py` — Notification model with 14 types (session, payment, chat, prescription, etc.)
- `utils.py` — Helper functions: notify_session_booked, notify_session_approved, notify_payment_done, notify_new_message, etc.
- `views.py` — notification_list, mark_read, mark_all_read, delete_notification, unread_count (live API)
- `urls.py` — Routes for all notification views
- `migrations/0001_initial.py`
- `templates/notifications/notification_list.html` — Full notifications page

## 3. therapy/views.py
- All views rewritten with full input validation
- `_is_session_joinable()` helper — uses IST time window (±15 min before, 90 min after)
- `video_call()` — blocks if outside time window with helpful message
- All session/payment/chat views now fire the correct notification
- `book_session()` — validates past dates, duplicate slots, self-booking
- All forms have proper error handling

## 4. therapy/context_processors.py
- Now also returns `notif_unread_count` for the bell badge

## 5. base.html
- Added notification bell icon with live badge in navbar
- Badge auto-updates every 30 seconds via JS polling

## 6. patient_dashboard.html + therapist_dashboard.html
- Join button replaced with time-locked button using `s.can_join`
- Shows lock icon + scheduled time when not in window
- Shows Join button only during the allowed time window (IST)

## Installation
```bash
python manage.py makemigrations notifications
python manage.py migrate
```
