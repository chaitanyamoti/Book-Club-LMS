from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.contrib.auth.models import User
from django.views.generic import UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from .forms import UserRegistrationForm, UserProfileForm, CustomLoginForm
from core.models import UserProfile
from notifications.utils import send_welcome_email
from notifications.forms import EmailPreferenceForm # Import the new form
from notifications.models import EmailPreference # Import the new model


def register_view(request):
    """User registration view"""
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)

            # Send welcome email, but don't let it block registration
            try:
                send_welcome_email(user)
                messages.success(request, 'Registration successful! Welcome to the Book Club.')
            except Exception as e:
                # Log the error (in a real app, use logging)
                print(f"Error sending welcome email: {e}")
                messages.warning(request, 'Registration successful, but could not send welcome email.')

            return redirect('/dashboard/')
    else:
        form = UserRegistrationForm()

    return render(request, 'registration/register.html', {'form': form})


def login_view(request):
    """Custom login view"""
    if request.user.is_authenticated:
        messages.info(request, 'You are already logged in.')
        return redirect('core:dashboard')

    if request.method == 'POST':
        form = CustomLoginForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data.get('email')
            password = form.cleaned_data.get('password')
            user = authenticate(request, username=email, password=password)

            if user is not None:
                login(request, user)
                messages.success(request, f'Welcome back, {user.get_full_name() or user.username}!')
                return redirect('/dashboard/')
            else:
                messages.error(request, 'Invalid email or password.')
    else:
        form = CustomLoginForm()

    return render(request, 'registration/login.html', {'form': form})


def logout_view(request):
    """Custom logout view"""
    logout(request)
    messages.info(request, 'You have been logged out successfully.')
    return redirect('core:home')


class ProfileView(LoginRequiredMixin, UpdateView):
    """User profile view"""
    model = UserProfile
    form_class = UserProfileForm
    template_name = 'dashboard/profile.html'
    success_url = reverse_lazy('core:dashboard')

    def get_object(self):
        return self.request.user.userprofile

    def form_valid(self, form):
        messages.success(self.request, 'Profile updated successfully!')
        return super().form_valid(form)


@login_required
@user_passes_test(lambda u: hasattr(u, "userprofile") and u.userprofile.role == "ADMIN")
def user_list_view(request):
    """Admin view to list all users"""
    users = User.objects.select_related('userprofile').all()
    return render(request, 'users/user_list.html', {'users': users})


@login_required
@user_passes_test(lambda u: hasattr(u, "userprofile") and u.userprofile.role == "ADMIN")
def toggle_user_status(request, user_id):
    """Admin view to activate/deactivate users"""
    user = get_object_or_404(User, id=user_id)
    user.userprofile.is_active = not user.userprofile.is_active
    user.userprofile.save()

    status = "activated" if user.userprofile.is_active else "deactivated"
    messages.success(request, f'User {user.get_full_name()} has been {status}.')

    return redirect('user_list')


@login_required
@user_passes_test(lambda u: hasattr(u, "userprofile") and u.userprofile.role == "ADMIN")
def change_user_role(request, user_id):
    """Admin view to change user role"""
    user = get_object_or_404(User, id=user_id)

    if request.method == 'POST':
        new_role = request.POST.get('role')
        if new_role in ['ADMIN', 'MEMBER']:
            user.userprofile.role = new_role
            user.userprofile.save()
    return redirect('user_list')

def public_profile_view(request, user_id):
    """Displays a user's public profile."""
    profile_user = get_object_or_404(User, id=user_id)
    return render(request, 'users/public_profile.html', {'profile_user': profile_user})

@login_required
def settings_view(request):
    """View for user settings, including email preferences."""
    email_preferences, created = EmailPreference.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        email_form = EmailPreferenceForm(request.POST, instance=email_preferences)
        if email_form.is_valid():
            email_form.save()
            messages.success(request, 'Your email preferences have been updated!')
            return redirect('users:settings')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        email_form = EmailPreferenceForm(instance=email_preferences)

    context = {
        'email_form': email_form,
    }
    return render(request, 'users/settings.html', context)


@login_required
def password_change_view(request):
    """Secure password change view"""
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            request.user.set_password(form.cleaned_data['new_password'])
            request.user.save()
            update_session_auth_hash(request, request.user)  # Keep user logged in

            # Update last password change
            request.user.userprofile.last_password_change = timezone.now()
            request.user.userprofile.save()

            # Log activity
            request.user.userprofile.add_activity_log(
                'password_changed',
                'Password was changed successfully',
                request.META.get('REMOTE_ADDR')
            )

            messages.success(request, 'Your password has been changed successfully!')
            return redirect('users:profile')
    else:
        form = PasswordChangeForm(request.user)

    return render(request, 'users/password_change.html', {'form': form})


@login_required
def email_change_view(request):
    """Email change view with verification"""
    if request.method == 'POST':
        form = EmailChangeForm(request.POST)
        if form.is_valid():
            new_email = form.cleaned_data['new_email']

            # Check if email is already taken
            if User.objects.filter(email=new_email).exclude(pk=request.user.pk).exists():
                messages.error(request, 'This email address is already in use.')
                return redirect('users:email_change')

            # Store pending email change (you might want to add a field for this)
            # For now, we'll just update it directly (in production, send verification email)
            old_email = request.user.email
            request.user.email = new_email
            request.user.save()

            # Log activity
            request.user.userprofile.add_activity_log(
                'email_changed',
                f'Email changed from {old_email} to {new_email}',
                request.META.get('REMOTE_ADDR')
            )

            messages.success(request, 'Your email address has been updated successfully!')
            return redirect('users:profile')
    else:
        form = EmailChangeForm()

    return render(request, 'users/email_change.html', {'form': form})


@login_required
def avatar_upload_view(request):
    """Avatar upload view"""
    if request.method == 'POST':
        form = AvatarUploadForm(request.POST, request.FILES, instance=request.user.userprofile)
        if form.is_valid():
            form.save()
            messages.success(request, 'Your avatar has been updated successfully!')
            return redirect('users:profile')
    else:
        form = AvatarUploadForm(instance=request.user.userprofile)

    return render(request, 'users/avatar_upload.html', {'form': form})


@login_required
def notification_preferences_view(request):
    """Notification preferences view"""
    if request.method == 'POST':
        form = NotificationPreferencesForm(request.POST, instance=request.user.userprofile)
        if form.is_valid():
            form.save()
            messages.success(request, 'Your notification preferences have been updated!')
            return redirect('users:profile')
    else:
        form = NotificationPreferencesForm(instance=request.user.userprofile)

    return render(request, 'users/notification_preferences.html', {'form': form})


@login_required
def session_management_view(request):
    """View active sessions (simplified - in production use proper session management)"""
    # This is a simplified version. In production, you'd track sessions properly
    context = {
        'current_session': {
            'device': request.META.get('HTTP_USER_AGENT', 'Unknown')[:50],
            'ip': request.META.get('REMOTE_ADDR', 'Unknown'),
            'login_time': request.session.get('login_time', 'Unknown'),
        }
    }
    return render(request, 'users/session_management.html', context)


@login_required
def audit_log_view(request):
    """Account activity log view"""
    activities = request.user.userprofile.get_activity_log()
    return render(request, 'users/audit_log.html', {'activities': activities})


@login_required
def account_deletion_view(request):
    """Account deletion view with confirmation"""
    if request.method == 'POST':
        form = AccountDeletionForm(request.POST)
        if form.is_valid():
            # Log deletion activity
            request.user.userprofile.add_activity_log(
                'account_deleted',
                'Account deletion requested',
                request.META.get('REMOTE_ADDR')
            )

            # In production, mark for deletion instead of immediate deletion
            # For now, we'll deactivate the account
            request.user.userprofile.is_active = False
            request.user.userprofile.save()

            # Log out user
            logout(request)
            messages.info(request, 'Your account has been deactivated. Contact admin to reactivate.')
            return redirect('core:home')
    else:
        form = AccountDeletionForm()

    return render(request, 'users/account_deletion.html', {'form': form})

