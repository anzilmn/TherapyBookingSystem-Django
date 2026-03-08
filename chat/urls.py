from django.urls import path
from . import views

urlpatterns = [
    # Main Chat Room (Handles View, Send, and Edit)
    path('room/<int:session_id>/', views.chat_room, name='chat_room'),
    
    # Delete Logic (Strictly for the message owner)
    path('delete-message/<int:message_id>/', views.delete_message, name='delete_message'),
]