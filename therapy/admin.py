from django.contrib import admin
from django.utils.html import format_html
from .models import TherapistProfile, Session, Review, ContactMessage, Complaint


@admin.register(TherapistProfile)
class TherapistAdmin(admin.ModelAdmin):
    list_display = ('user', 'specialization', 'is_approved', 'is_blocked', 'block_reason_short')
    list_filter = ('is_approved', 'is_blocked')
    actions = ['approve_therapists', 'block_therapists', 'unblock_therapists']

    def block_reason_short(self, obj):
        return (obj.block_reason[:60] + '…') if obj.block_reason and len(obj.block_reason) > 60 else (obj.block_reason or '—')
    block_reason_short.short_description = 'Block Reason'

    def approve_therapists(self, request, queryset):
        queryset.update(is_approved=True)
    approve_therapists.short_description = "✅ Approve selected therapists"

    def block_therapists(self, request, queryset):
        queryset.update(is_blocked=True)
    block_therapists.short_description = "🚫 Block selected therapists"

    def unblock_therapists(self, request, queryset):
        queryset.update(is_blocked=False, block_reason=None)
    unblock_therapists.short_description = "✅ Unblock selected therapists"


@admin.register(Complaint)
class ComplaintAdmin(admin.ModelAdmin):
    list_display = ('id', 'patient_name', 'therapist_name', 'subject', 'status', 'created_at', 'block_action')
    list_filter = ('status',)
    readonly_fields = ('session', 'patient', 'therapist', 'subject', 'description', 'created_at')
    fields = ('session', 'patient', 'therapist', 'subject', 'description', 'status', 'created_at')
    ordering = ('-created_at',)
    actions = ['mark_reviewed', 'mark_resolved', 'block_complained_therapist', 'unblock_complained_therapist']

    def patient_name(self, obj):
        return obj.patient.username
    patient_name.short_description = 'Patient'

    def therapist_name(self, obj):
        return obj.therapist.username
    therapist_name.short_description = 'Therapist'

    def block_action(self, obj):
        try:
            profile = obj.therapist.therapist_info
            if profile.is_blocked:
                return format_html('<span style="color:red;font-weight:bold;">🚫 BLOCKED</span>')
            else:
                return format_html('<span style="color:green;">✅ Active</span>')
        except Exception:
            return '—'
    block_action.short_description = 'Therapist Status'

    def mark_reviewed(self, request, queryset):
        queryset.update(status='reviewed')
    mark_reviewed.short_description = "Mark selected complaints as Reviewed"

    def mark_resolved(self, request, queryset):
        queryset.update(status='resolved')
    mark_resolved.short_description = "Mark selected complaints as Resolved"

    def block_complained_therapist(self, request, queryset):
        blocked = 0
        for complaint in queryset:
            try:
                profile = complaint.therapist.therapist_info
                reason = f"Blocked due to complaint #{complaint.id}: {complaint.subject}"
                profile.is_blocked = True
                profile.block_reason = reason
                profile.save()
                complaint.status = 'resolved'
                complaint.save()
                blocked += 1
            except Exception:
                pass
        self.message_user(request, f"🚫 {blocked} therapist(s) have been blocked.")
    block_complained_therapist.short_description = "🚫 Block therapist(s) for selected complaints"

    def unblock_complained_therapist(self, request, queryset):
        unblocked = 0
        for complaint in queryset:
            try:
                profile = complaint.therapist.therapist_info
                profile.is_blocked = False
                profile.block_reason = None
                profile.save()
                unblocked += 1
            except Exception:
                pass
        self.message_user(request, f"✅ {unblocked} therapist(s) have been unblocked.")
    unblock_complained_therapist.short_description = "✅ Unblock therapist(s) for selected complaints"


admin.site.register(Session)
admin.site.register(Review)
admin.site.register(ContactMessage)
