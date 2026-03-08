from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from .models import Profile
from therapy.models import TherapistProfile

# 1. Inline for the Profile (Picture/Role)
class ProfileInline(admin.StackedInline):
    model = Profile
    can_delete = False
    verbose_name_plural = 'General Profile Info'

# 2. Inline for the Therapist Details (Bio/Cert)
class TherapistProfileInline(admin.StackedInline):
    model = TherapistProfile
    can_delete = False
    verbose_name_plural = 'Therapist Professional Info'

# 3. Custom User Admin that brings it all together
class UserAdmin(BaseUserAdmin):
    inlines = (ProfileInline, TherapistProfileInline)
    list_display = ('username', 'email', 'get_role', 'is_staff')

    def get_role(self, obj):
        return obj.profile.role
    get_role.short_description = 'Role'

# Re-register User
admin.site.unregister(User)
admin.site.register(User, UserAdmin)