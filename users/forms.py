from django import forms
from django.contrib.auth.forms import UserCreationForm, PasswordChangeForm
from django.contrib.auth import get_user_model
from core.models import UserProfile

User = get_user_model()


class UserRegistrationForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2')

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        # Use email as username if username is empty
        if not user.username:
            user.username = user.email
        if commit:
            user.save()
        return user


class CustomLoginForm(forms.Form):
    email = forms.EmailField()
    password = forms.CharField(widget=forms.PasswordInput)


class UserProfileForm(forms.ModelForm):
    """Profile form excluding sensitive security fields"""
    class Meta:
        model = UserProfile
        fields = ['phone', 'reading_preferences']  # Removed role, streak_days, longest_streak, is_active

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make sure role is never included in the form
        if 'role' in self.fields:
            del self.fields['role']
        if 'streak_days' in self.fields:
            del self.fields['streak_days']
        if 'longest_streak' in self.fields:
            del self.fields['longest_streak']
        if 'is_active' in self.fields:
            del self.fields['is_active']

    def clean_reading_preferences(self):
        """Validate reading preferences field to prevent XSS"""
        reading_preferences = self.cleaned_data.get('reading_preferences')
        if reading_preferences:
            # Check for HTML/script tags
            import re
            if re.search(r'<[^>]+>', reading_preferences):
                raise forms.ValidationError("HTML or script content is not allowed in reading preferences.")
            # Check for script keywords
            if 'script' in reading_preferences.lower() or 'javascript:' in reading_preferences.lower():
                raise forms.ValidationError("Script content is not allowed in reading preferences.")
        return reading_preferences


class PasswordChangeForm(forms.Form):
    """Secure password change form"""
    current_password = forms.CharField(widget=forms.PasswordInput, label="Current Password")
    new_password = forms.CharField(widget=forms.PasswordInput, label="New Password")
    confirm_password = forms.CharField(widget=forms.PasswordInput, label="Confirm New Password")

    def __init__(self, user, *args, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)

    def clean_current_password(self):
        current_password = self.cleaned_data.get('current_password')
        if not self.user.check_password(current_password):
            raise forms.ValidationError("Current password is incorrect.")
        return current_password

    def clean(self):
        cleaned_data = super().clean()
        new_password = cleaned_data.get('new_password')
        confirm_password = cleaned_data.get('confirm_password')

        if new_password and confirm_password:
            if new_password != confirm_password:
                raise forms.ValidationError("New passwords do not match.")
            if len(new_password) < 12:
                raise forms.ValidationError("Password must be at least 12 characters long.")
            # Add more password strength validation as needed

        return cleaned_data


class EmailChangeForm(forms.Form):
    """Email change form with verification"""
    new_email = forms.EmailField(label="New Email Address")
    confirm_email = forms.EmailField(label="Confirm New Email Address")

    def clean(self):
        cleaned_data = super().clean()
        new_email = cleaned_data.get('new_email')
        confirm_email = cleaned_data.get('confirm_email')

        if new_email and confirm_email:
            if new_email != confirm_email:
                raise forms.ValidationError("Email addresses do not match.")

        return cleaned_data


class AvatarUploadForm(forms.ModelForm):
    """Avatar upload form"""
    class Meta:
        model = UserProfile
        fields = ['avatar']


class NotificationPreferencesForm(forms.ModelForm):
    """Notification preferences form"""
    class Meta:
        model = UserProfile
        fields = [
            'email_overdue_reminders', 'email_due_date_alerts',
            'email_book_returned', 'email_new_announcements', 'email_weekly_digest'
        ]


class AccountDeletionForm(forms.Form):
    """Account deletion confirmation form"""
    confirm_deletion = forms.CharField(
        label="Type 'DELETE' to confirm",
        help_text="This action cannot be undone. All your data will be permanently deleted."
    )

    def clean_confirm_deletion(self):
        confirm_text = self.cleaned_data.get('confirm_deletion')
        if confirm_text != 'DELETE':
            raise forms.ValidationError("Please type 'DELETE' to confirm account deletion.")
        return confirm_text
