from django.db import models
from django.contrib.auth.models import User

class TherapistProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='therapist_info')
    qualification = models.CharField(max_length=255)
    experience_years = models.PositiveIntegerField(default=0)
    specialization = models.CharField(max_length=100)
    bio = models.TextField()
    certificate = models.FileField(upload_to='certificates/')
    is_approved = models.BooleanField(default=False)
    is_blocked = models.BooleanField(default=False)
    block_reason = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"Dr. {self.user.last_name} ({self.specialization})"
    

class Session(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    )
    # VRO: Added choices for session type
    TYPE_CHOICES = (
        ('single', 'Single Session'),
        ('couple', 'Couple Session'),
    )

    patient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='patient_sessions')
    therapist = models.ForeignKey(User, on_delete=models.CASCADE, related_name='therapist_sessions')
    date = models.DateField()
    time_slot = models.TimeField()
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='pending')
    
    # --- VRO: NEW FIELD FOR TYPE ---
    session_type = models.CharField(max_length=10, choices=TYPE_CHOICES, default='single')
    # -------------------------------

    notes = models.TextField(blank=True, null=True) 
    
    amount = models.DecimalField(max_digits=10, decimal_places=2, default=500.00)
    is_paid = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.session_type} Session: {self.patient.username} with {self.therapist.username}"
    

class Review(models.Model):
    session = models.OneToOneField(Session, on_delete=models.CASCADE, related_name='review')
    rating = models.IntegerField(choices=[(i, i) for i in range(1, 6)])
    comment = models.TextField()

# VRO: I removed the Message model from here to fix the Reverse Accessor error.

class ContactMessage(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField()
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_resolved = models.BooleanField(default=False)

    def __str__(self):
        return f"Message from {self.name} - {self.email}"
    



class Prescription(models.Model):
    session = models.OneToOneField(Session, on_delete=models.CASCADE, related_name='prescription')
    diagnosis = models.TextField(help_text="What is the issue?")
    advice = models.TextField(help_text="General mental health advice")
    medicines = models.TextField(blank=True, null=True, help_text="List medicines if any")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Prescription for {self.session.patient.username}"    
    



from django.db import models
from django.contrib.auth.models import User

class JournalEntry(models.Model):
    MOOD_CHOICES = [
        (5, '😊'),
        (4, '🙂'),
        (3, '😐'),
        (2, '😔'),
        (1, '😭'),
    ]
    
    patient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='journal_entries')
    content = models.TextField()
    mood_score = models.IntegerField(choices=MOOD_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.patient.username}'s entry on {self.created_at.date()}"

class Complaint(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('reviewed', 'Reviewed'),
        ('resolved', 'Resolved'),
    )
    session = models.OneToOneField(Session, on_delete=models.CASCADE, related_name='complaint')
    patient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='complaints_filed')
    therapist = models.ForeignKey(User, on_delete=models.CASCADE, related_name='complaints_received')
    subject = models.CharField(max_length=200)
    description = models.TextField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Complaint by {self.patient.username} against {self.therapist.username} [{self.status}]"
