from django.urls import path
from . import views

urlpatterns = [
    path('', views.notification_list, name='notification_list'),
    path('<int:notif_id>/read/', views.mark_read, name='mark_notif_read'),
    path('mark-all-read/', views.mark_all_read, name='mark_all_notif_read'),
    path('<int:notif_id>/delete/', views.delete_notification, name='delete_notification'),
    path('unread-count/', views.unread_count, name='notif_unread_count'),
]
