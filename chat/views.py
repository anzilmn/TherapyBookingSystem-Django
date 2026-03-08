from django.shortcuts import render, get_object_or_404, redirect
from therapy.models import Session
from .models import Message
from django.contrib.auth.decorators import login_required
from django.contrib import messages

@login_required
def chat_room(request, session_id):
    session = get_object_or_404(Session, id=session_id)
    if request.user not in [session.patient, session.therapist]:
        return redirect('dashboard')

    # Mark others' messages as read
    Message.objects.filter(session=session, is_read=False).exclude(sender=request.user).update(is_read=True)

    # --- EDIT LOGIC ---
    edit_id = request.GET.get('edit')
    edit_msg = None
    if edit_id:
        # Strict validation: Only sender can edit
        edit_msg = get_object_or_404(Message, id=edit_id, sender=request.user)

    if request.method == 'POST':
        # Payment check for patients
        if request.user == session.patient and not session.is_paid:
            messages.error(request, "Vro, complete payment to chat!")
            return redirect('initiate_payment', session_id=session.id)

        content = request.POST.get('content')
        attachment = request.FILES.get('attachment')
        voice_note = request.FILES.get('voice_note')
        msg_id = request.POST.get('msg_id')

        if msg_id:
            # UPDATE existing message (Strict validation)
            msg_to_edit = get_object_or_404(Message, id=msg_id, sender=request.user)
            msg_to_edit.content = content
            msg_to_edit.is_edited = True
            msg_to_edit.save()
        elif content or attachment or voice_note:
            # CREATE new message
            Message.objects.create(
                session=session,
                sender=request.user,
                content=content,
                attachment=attachment,
                voice_note=voice_note
            )
        return redirect('chat_room', session_id=session_id)

    chat_messages = Message.objects.filter(session=session)
    return render(request, 'chat/chat_room.html', {
        'session': session,
        'chat_messages': chat_messages,
        'edit_msg': edit_msg
    })

@login_required
def delete_message(request, message_id):
    # Strict validation: Only sender can delete their own message
    msg = get_object_or_404(Message, id=message_id, sender=request.user)
    s_id = msg.session.id
    msg.delete()
    return redirect('chat_room', session_id=s_id)