from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.contrib import messages  # Import this for the popups!
from django.contrib.auth.decorators import login_required
from .forms import SignUpForm

def signup(request):
    if request.method == 'POST':
        form = SignUpForm(request.POST) 
        if form.is_valid():
            user = form.save()
            login(request, user)
            
            # 🟢 SUCCESS MSG: User registered
            messages.success(request, f"Welcome to MindCare, {user.username}! Your account was created successfully.")
            return redirect('dashboard_redirect')
        else:
            # 🔴 INVALID MSG: Form errors (like password too short)
            messages.error(request, "Registration failed. Please correct the errors below.")
    else:
        form = SignUpForm()
    return render(request, 'accounts/signup.html', {'form': form})

def logout_view(request):
    logout(request)
    # 🔵 INFO MSG: User logged out
    messages.info(request, "You have been logged out. See you soon!")
    return redirect('login')

@login_required
def dashboard_redirect(request):
    """The traffic controller: Sends users to the right dashboard without spamming."""
    
    # Message removed from here because this view runs every time 
    # you click 'Dashboard' in the navbar.

    try:
        # Check the role from the Profile model
        role = request.user.profile.role
        
        if role == 'therapist':
            return redirect('therapist_dashboard')
        elif role == 'admin':
            return redirect('/admin/')
        else:
            return redirect('patient_dashboard')
            
    except Exception as e:
        messages.error(request, "Profile configuration error. Please contact support.")
        return redirect('index')