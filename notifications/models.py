from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User # Import User model
import uuid # Import uuid for UUIDField

class EmailLog(models.Model):
    EMAIL_TYPES = [
        ('WELCOME', 'Welcome Email'),
        ('OVERDUE', 'Overdue Alert'),
        ('BOOK_ISSUED', 'Book Issued'),
        ('BOOK_RETURNED', 'Book Returned'),
        ('NEW_BOOK_ALERT', 'New Book Alert'),
        ('READING_STREAK', 'Reading Streak'),
        ('BOOKS_READ_MILESTONE', 'Books Read Milestone'),
        ('GENERAL', 'General Notification'),
    ]

    STATUS_CHOICES = [
        ('SENT', 'Sent Successfully'),
        ('FAILED', 'Failed to Send'),
        ('PENDING', 'Pending'),
    ]

    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='email_logs')
    email_type = models.CharField(max_length=40, choices=EMAIL_TYPES)
    subject = models.CharField(max_length=255)
    recipient = models.EmailField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='PENDING')
    error_message = models.TextField(blank=True, null=True)
    sent_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    email_content = models.TextField(blank=True, null=True)  # Store the HTML content for debugging
    opened_at = models.DateTimeField(null=True, blank=True)
    clicked_links = models.JSONField(default=dict)
    user_agent = models.TextField(blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    ab_test_variant = models.CharField(max_length=50, blank=True, null=True)
    campaign_id = models.CharField(max_length=100, blank=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name_plural = "Email Logs"

    def __str__(self):
        return f"{self.email_type} to {self.recipient} - {self.status}"

class Announcement(models.Model):
    title = models.CharField(max_length=200)
    content = models.TextField()
    pub_date = models.DateTimeField(default=timezone.now)
    end_date = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    display_on_homepage = models.BooleanField(default=False) # If true, show on homepage/dashboard

    class Meta:
        ordering = ['-pub_date']
        verbose_name_plural = "Announcements"

    def __str__(self):
        return self.title

class UserNotification(models.Model):
    NOTIFICATION_TYPES = [
        ('INFO', 'Information'),
        ('WARNING', 'Warning'),
        ('ALERT', 'Alert'),
        ('OVERDUE', 'Overdue Reminder'),
        ('NEW_BOOK', 'New Book Available'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)
    link_url = models.URLField(null=True, blank=True)
    type = models.CharField(max_length=10, choices=NOTIFICATION_TYPES, default='INFO')

    class Meta:
        ordering = ['-created_at']
        verbose_name_plural = "User Notifications"

    def __str__(self):
        return f"Notification for {self.user.username}: {self.message[:50]}..."


class EmailPreference(models.Model):
    FREQUENCY_CHOICES = [
        ('IMMEDIATE', 'Immediate'),
        ('DAILY', 'Daily Digest'),
        ('WEEKLY', 'Weekly Summary'),
        ('MONTHLY', 'Monthly Newsletter'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    welcome_emails = models.BooleanField(default=True)
    transaction_emails = models.BooleanField(default=True)
    reading_emails = models.BooleanField(default=True)
    community_emails = models.BooleanField(default=True)
    marketing_emails = models.BooleanField(default=True)
    frequency = models.CharField(max_length=20, choices=FREQUENCY_CHOICES, default='IMMEDIATE')

    def __str__(self):
        return f"Email Preferences for {self.user.username}"
