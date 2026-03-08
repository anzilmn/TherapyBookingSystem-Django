# accounts/forms.py
from django import forms
from django.contrib.auth.models import User
from .models import Profile

class SignUpForm(forms.ModelForm):
    # This removes 'Admin' from the signup page!
    role = forms.ChoiceField(choices=Profile.PUBLIC_ROLES, required=True)
    password = forms.CharField(widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = ['username', 'email', 'password']

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password"])
        if commit:
            user.save() # This triggers the signal
            # Now we update the profile the signal just made
            profile = user.profile
            profile.role = self.cleaned_data['role']
            profile.save()
        return user