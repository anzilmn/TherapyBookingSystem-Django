from django.urls import path
from . import views

urlpatterns = [
    # General Routes
    path('', views.index, name='index'), 
    path('dashboard/', views.dashboard_redirect, name='dashboard'), 

    # Therapist Routes
    path('therapist/dashboard/', views.therapist_dashboard, name='therapist_dashboard'),
    path('therapist/complete-profile/', views.complete_profile, name='complete_profile'),

    # Patient Routes
    path('patient/dashboard/', views.patient_dashboard, name='patient_dashboard'),
    path('book/<int:therapist_id>/', views.book_session, name='book_session'),
    
    # --- JOURNAL ROUTE (ADDED THIS) ---
    path('journal/', views.journal_view, name='journal'), 
    
    # --- NEW PAYMENT SYSTEM ROUTES ---
    path('session/<int:session_id>/pay/', views.initiate_payment, name='initiate_payment'),
    path('session/<int:session_id>/process-payment/', views.process_payment, name='process_payment'),

    # Feedback & Chat Routes
    path('session/<int:session_id>/review/', views.give_feedback, name='give_feedback'),
    path('session/<int:session_id>/complaint/', views.file_complaint, name='file_complaint'),
    path('chat/<int:session_id>/', views.chat_room, name='chat_room'),
    path('session/<int:session_id>/video-call/', views.video_call, name='video_call'),
    path('session/update/<int:session_id>/<str:action>/', views.update_session, name='update_session'),
    path('experts/', views.therapist_list, name='therapist_list'),
    path('session/delete/<int:session_id>/', views.delete_session, name='delete_session'),
    path('session/edit/<int:session_id>/', views.edit_session, name='edit_session'),
    path('session/<int:session_id>/prescribe/', views.add_prescription, name='add_prescription'),
    path('session/<int:session_id>/prescription/view/', views.view_prescription, name='view_prescription'),
    path('session/<int:session_id>/prescription/download/', views.download_prescription, name='download_prescription'),
    path('emergency/', views.emergency_support, name='emergency_support'),
    path('book/<int:therapist_id>/choose-type/', views.choose_session_type, name='choose_session_type'),
]