from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

# accounts/models.py
class Profile(models.Model):
    # Public choices for signup
    PUBLIC_ROLES = (
        ('therapist', 'Therapist'),
        ('patient', 'Patient'),
    )
    # Internal choices including Admin
    ROLE_CHOICES = (('admin', 'Admin'),) + PUBLIC_ROLES

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='patient')
    profile_pic = models.ImageField(upload_to='profile_pics/', null=True, blank=True)
    phone = models.CharField(max_length=15, blank=True)

    def __str__(self):
        return f"{self.user.username} - {self.role}"

# --- SIGNALS ---
@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        # Check if profile already exists to avoid errors
        Profile.objects.get_or_create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    instance.profile.save()





from django.contrib.auth.signals import user_logged_in
from django.dispatch import receiver
from django.contrib import messages

@receiver(user_logged_in)
def show_login_message(sender, request, user, **kwargs):
    # This will trigger NO MATTER how the user logs in
    messages.success(request, f"Welcome back, {user.username}! Logged in successfully.")
