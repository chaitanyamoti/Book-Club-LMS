from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.http import JsonResponse
from django.db import models
from django.utils import timezone
from django.views.generic import ListView # Consolidated ListView import
from django.http import HttpResponse # Import HttpResponse for tracking pixel
from .models import Announcement, UserNotification, EmailLog # Consolidated model imports and added EmailLog
from .utils import send_welcome_email, send_overdue_alerts # Consolidated utility imports


@login_required
def notifications_dashboard(request):
    """Show notification actions and status."""
    return render(request, 'notifications/notifications_dashboard.html')

@login_required
def send_welcome(request):
    if request.method == 'POST':
        user = request.user
        ok = send_welcome_email(user)
        if ok:
            messages.success(request, 'Welcome email sent!')
        else:
            messages.error(request, 'No email found for your user.')
        return redirect('notifications:dashboard')
    return JsonResponse({'error': 'POST only'})

@login_required
def send_overdue(request):
    # Restrict this action to staff/admin users only
    if not request.user.is_staff:
        messages.error(request, 'You do not have permission to send overdue alerts.')
        return redirect('notifications:dashboard')

    if request.method == 'POST':
        sent = send_overdue_alerts()
        messages.success(request, f'Sent overdue alerts to {sent} users.')
        return redirect('notifications:dashboard')
    return JsonResponse({'error': 'POST only'})


class AnnouncementListView(LoginRequiredMixin, ListView): # Added LoginRequiredMixin
    model = Announcement
    template_name = 'notifications/announcement_list.html'
    context_object_name = 'announcements'
    login_url = 'users:login' # Specify the login URL

    def get_queryset(self):
        today = timezone.now()
        return Announcement.objects.filter(
            is_active=True,
            pub_date__lte=today,
        ).filter( # Apply Q objects in a separate filter call
            models.Q(end_date__isnull=True) | models.Q(end_date__gte=today)
        ).order_by('-pub_date')


class UserNotificationListView(LoginRequiredMixin, ListView):
    model = UserNotification
    template_name = 'notifications/user_notification_list.html'
    context_object_name = 'user_notifications'

    def get_queryset(self):
        queryset = UserNotification.objects.filter(user=self.request.user).order_by('-created_at')
        # Mark all displayed notifications as read
        queryset.update(is_read=True)
        return queryset

def track_email_open(request, email_log_uuid):
    """
    View to track email opens.
    A 1x1 transparent GIF is returned.
    """
    try:
        email_log = EmailLog.objects.get(uuid=email_log_uuid)
        if not email_log.opened_at:
            email_log.opened_at = timezone.now()
            email_log.save()
    except EmailLog.DoesNotExist:
        # Log this error if necessary, but don't break the user experience
        pass

    # Return a 1x1 transparent GIF
    response = HttpResponse(
        b"GIF89a\x01\x00\x01\x00\x80\x00\x00\xff\xff\xff\x00\x00\x00,\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02D\x01\x00;",
        content_type="image/gif",
    )
    return response


import base64

def track_click(request, email_log_uuid, redirect_url_base64):
    """
    View to track email link clicks.
    Logs the click and redirects to the original URL.
    """
    try:
        redirect_url = base64.urlsafe_b64decode(redirect_url_base64).decode('utf-8')
        email_log = EmailLog.objects.get(uuid=email_log_uuid)
        
        # Log the clicked link
        if redirect_url not in email_log.clicked_links:
            email_log.clicked_links[redirect_url] = str(timezone.now())
            email_log.save()
            
        return redirect(redirect_url)

    except (EmailLog.DoesNotExist, TypeError, ValueError):
        # Fail gracefully, redirect to a safe default page
        return redirect('/')
