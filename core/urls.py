from django.contrib import admin, messages
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views
from therapy import views as therapy_views 

class MyLoginView(auth_views.LoginView):
    template_name = 'accounts/login.html'
    
    def form_valid(self, form):
        username = form.get_user().username
        messages.success(self.request, f"Welcome back, {username}! Logged in successfully.")
        return super().form_valid(form)

    def form_invalid(self, form):
        # This sends a message to the 'messages' framework
        messages.error(self.request, "Invalid username or password. Please try again.")
        return super().form_invalid(form)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('login/', MyLoginView.as_view(), name='login'),
    path('', therapy_views.index, name='home'), 
    path('accounts/', include('accounts.urls')),
    path('therapy/', include('therapy.urls')), 
    path('chat/', include('chat.urls')),
    path('notifications/', include('notifications.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)