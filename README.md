# 🧠 TherapyApp — Online Mental Health Platform

A full-stack web application built with **Django** that connects patients with verified therapists. Supports session booking, video calls, real-time chat, payments, prescriptions, journaling, and complaint management — all with IST time-based access controls.

---

## 🚀 Features

### 👤 Authentication & Roles
- Signup / Login with role selection — **Patient** or **Therapist**
- Admin role managed via Django admin panel
- Auto profile creation via signals on user registration

### 🩺 Therapist
- Complete profile with qualification, specialization, experience, bio & certificate upload
- Admin approval required before going live
- Dashboard showing all patient bookings with status, payment, last message
- Accept / Reject incoming session requests
- **IST time-locked actions** — Join, Chat, and Finish buttons unlock only at the correct session time
  - Join & Chat unlock 15 min before session start, up to 90 min after
  - **Finish button unlocks only after the session ends** (start time + 1 hour)
- Add prescription for completed sessions
- Account block screen — blocked therapists see suspension reason and cannot access anything

### 🙋 Patient
- Browse verified therapists
- Book sessions — Single or Couple type
- Choose from available time slots (9 AM – 8 PM with breaks)
- Reschedule or cancel pending sessions
- Simulated payment gateway — unlocks session on payment
- After payment, redirected to **patient dashboard** (not chat)
- Rate & review therapists after session completion
- **File a complaint** against a therapist after session — goes to admin for review
- View & download PDF prescription
- Emergency support page
- Mood journal with emoji mood tracker and weekly mood chart

### 💬 Chat & Video
- Real-time chat room per session (time-locked to session window)
- Unread message badge on therapist dashboard
- Voice note & file attachment support in chat
- Video call room (time-locked to session window)

### 💳 Payments
- Simulated payment flow with method selection
- Marks session as paid and unlocks all session features

### 🔔 Notifications
- In-app notifications for: session booked, approved, cancelled, completed, payment done, prescription added, review received

### 📋 Complaint System
- Patient can file one complaint per completed session
- Complaint includes subject + detailed description
- Admin sees all complaints in a dedicated panel
- Admin can **block** or **unblock** therapist directly from a complaint
- Blocked therapist sees a styled suspension page with the block reason on login
- "Complaint Filed ✅" indicator shown on patient dashboard after submission

### 🛠️ Admin Panel
- Approve / block / unblock therapists
- Manage complaints — mark as Reviewed or Resolved
- View all sessions, reviews, contact messages

---

## 🗂️ Project Structure

```
therapy_final/
├── accounts/          # Auth, signup, profile, roles
├── therapy/           # Core app — sessions, booking, reviews, complaints
├── chat/              # Chat messages, attachments, voice notes
├── notifications/     # In-app notification system
├── core/              # Django settings, root URLs
└── templates/         # All HTML templates
```

---

## ⚙️ Setup & Installation

```bash
# 1. Clone the repo
git clone https://github.com/yourusername/therapyapp.git
cd therapyapp/therapy_final

# 2. Create and activate virtual environment
python -m venv venv

# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate

# 3. Install dependencies
pip install django pillow

# 4. Apply migrations
python manage.py migrate

# 5. Create a superuser (admin)
python manage.py createsuperuser

# 6. Run the development server
python manage.py runserver
```

Then open [http://127.0.0.1:8000](http://127.0.0.1:8000)

---

## 🔐 Admin Setup

1. Go to [http://127.0.0.1:8000/admin](http://127.0.0.1:8000/admin)
2. Log in with your superuser credentials
3. Approve therapist accounts under **Therapist Profiles**
4. Manage complaints and block/unblock therapists under **Complaints**

---

## 🕐 Time Slots Available

| Slot | Time |
|------|------|
| Morning | 9 AM – 10 AM |
| Morning | 10 AM – 11 AM |
| Morning | 11 AM – 12 PM |
| Afternoon | 1 PM – 2 PM |
| Afternoon | 2 PM – 3 PM |
| Afternoon | 3 PM – 4 PM |
| Evening | 4 PM – 5 PM |
| Evening | 5 PM – 6 PM |
| Night | 7 PM – 8 PM |

All times are in **IST (Asia/Kolkata)**.

---

## 🧱 Models Overview

| Model | App | Purpose |
|---|---|---|
| `Profile` | accounts | Stores user role (patient/therapist) and profile pic |
| `TherapistProfile` | therapy | Therapist details, approval, block status |
| `Session` | therapy | Booking record with date, time slot, type, payment |
| `Review` | therapy | One review per completed session |
| `Complaint` | therapy | One complaint per completed session, reviewed by admin |
| `Prescription` | therapy | Diagnosis, advice, medicines per session |
| `JournalEntry` | therapy | Patient mood journal entries |
| `ContactMessage` | therapy | Landing page contact form submissions |
| `Message` | chat | Chat messages with attachment and voice note support |
| `Notification` | notifications | In-app notification records per user |

---

## 🖥️ Tech Stack

- **Backend** — Django 4.x, Python 3.11
- **Database** — SQLite (dev) — easily swappable to PostgreSQL
- **Frontend** — Bootstrap 5, Bootstrap Icons, Chart.js
- **Auth** — Django built-in auth + custom role system
- **PDF** — Django template-based prescription rendering
- **Time handling** — `zoneinfo` for IST-aware time comparisons

---

## 📸 Pages

- `/` — Landing page with therapist listing & contact form
- `/therapy/patient/dashboard/` — Patient session dashboard
- `/therapy/therapist/dashboard/` — Therapist patient management
- `/therapy/experts/` — Browse all verified therapists
- `/therapy/book/<id>/` — Book a session
- `/therapy/journal/` — Mood journal
- `/therapy/emergency/` — Emergency support resources
- `/admin/` — Django admin panel

---

## 📄 License

MIT License — free to use, modify and distribute.



 python -m venv venv
.\venv\Scripts\activate
pip install django
pip install pillow
