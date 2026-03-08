from django.db import models
from django.contrib.auth.models import User
from therapy.models import Session

class Message(models.Model):
    session = models.ForeignKey(Session, on_delete=models.CASCADE, related_name='chat_messages')
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_chat_messages') 
    
    # Text content can now be empty if sending only a file or voice note
    content = models.TextField(blank=True, null=True)
    
    # --- WHATSAPP FEATURES ---
    attachment = models.FileField(upload_to='chat_attachments/', blank=True, null=True)
    voice_note = models.FileField(upload_to='chat_voice/', blank=True, null=True)
    
    is_read = models.BooleanField(default=False)
    is_edited = models.BooleanField(default=False)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['timestamp']

    def __str__(self):
        return f"From {self.sender.username} at {self.timestamp}"

    @property
    def is_image(self):
        if self.attachment:
            return self.attachment.name.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.webp'))
        return False