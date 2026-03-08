# accounts/urls.py
from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('signup/', views.signup, name='signup'),
    
    # Login stays standard
    path('login/', auth_views.LoginView.as_view(template_name='accounts/login.html'), name='login'),
    
    # Point this to your CUSTOM logout view in views.py
    path('logout/', views.logout_view, name='logout'), 
    
    # The central traffic controller
    path('dashboard/redirect/', views.dashboard_redirect, name='dashboard_redirect'),
]