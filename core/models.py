from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator
import uuid
import json

# User Profile Model
class UserProfile(models.Model):
    ROLE_CHOICES = [
        ('ADMIN', 'Admin'),
        ('MEMBER', 'Member'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    phone = models.CharField(max_length=15, blank=True, null=True)
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='MEMBER')
    reading_preferences = models.TextField(blank=True)
    streak_days = models.IntegerField(default=0)
    longest_streak = models.IntegerField(default=0)
    last_reading_date = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    # Notification preferences
    email_overdue_reminders = models.BooleanField(default=True)
    email_due_date_alerts = models.BooleanField(default=True)
    email_book_returned = models.BooleanField(default=True)
    email_new_announcements = models.BooleanField(default=True)
    email_weekly_digest = models.BooleanField(default=False)
    reminder_days_before_due = models.IntegerField(default=3)
    total_books_read = models.IntegerField(default=0) # New field for tracking total books read

    # Security & Authentication Fields
    two_factor_enabled = models.BooleanField(default=False)
    two_factor_secret = models.CharField(max_length=32, blank=True, null=True)
    backup_codes = models.TextField(blank=True, null=True)  # JSON list of backup codes
    last_password_change = models.DateTimeField(null=True, blank=True)
    backup_email = models.EmailField(blank=True, null=True)
    recovery_phone = models.CharField(max_length=15, blank=True, null=True)

    # Session Management
    last_login_ip = models.GenericIPAddressField(null=True, blank=True)
    last_login_device = models.CharField(max_length=200, blank=True, null=True)

    # Audit Log (JSON field for storing account activity)
    account_activity_log = models.TextField(blank=True, null=True)  # JSON list of activities

    def __str__(self):
        return f"{self.user.username} - {self.role}"

    def get_backup_codes(self):
        """Get backup codes as list"""
        if self.backup_codes:
            try:
                return json.loads(self.backup_codes)
            except:
                return []
        return []

    def set_backup_codes(self, codes):
        """Set backup codes as JSON"""
        self.backup_codes = json.dumps(codes)

    def add_activity_log(self, activity_type, details=None, ip_address=None):
        """Add entry to activity log"""
        log_entry = {
            'timestamp': timezone.now().isoformat(),
            'type': activity_type,
            'details': details or '',
            'ip_address': ip_address or ''
        }

        current_log = []
        if self.account_activity_log:
            try:
                current_log = json.loads(self.account_activity_log)
            except:
                current_log = []

        current_log.insert(0, log_entry)  # Add to beginning

        # Keep only last 100 entries
        if len(current_log) > 100:
            current_log = current_log[:100]

        self.account_activity_log = json.dumps(current_log)
        self.save(update_fields=['account_activity_log'])

    def get_activity_log(self, limit=30):
        """Get recent activity log entries"""
        if self.account_activity_log:
            try:
                log = json.loads(self.account_activity_log)
                return log[:limit]
            except:
                return []
        return []

    class Meta:
        verbose_name = "User Profile"
        verbose_name_plural = "User Profiles"

# Book Model
class Book(models.Model):
    STATUS_CHOICES = [
        ('AVAILABLE', 'Available'),
        ('ISSUED', 'Issued'),
        ('OVERDUE', 'Overdue'),
        ('LOST', 'Lost'),
        ('DAMAGED', 'Damaged'),
    ]

    title = models.CharField(max_length=200)
    author = models.CharField(max_length=100)
    isbn = models.CharField(max_length=13, unique=True, blank=True, null=True)
    genre = models.CharField(max_length=50, blank=True)
    description = models.TextField(blank=True)
    cover_image = models.ImageField(upload_to='book_covers/', blank=True, null=True)
    cover_url = models.URLField(blank=True)
    qr_code = models.ImageField(upload_to='qr_codes/', blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='AVAILABLE')
    added_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    added_date = models.DateTimeField(auto_now_add=True)
    total_copies = models.IntegerField(default=1, validators=[MinValueValidator(1)])
    available_copies = models.IntegerField(default=1, validators=[MinValueValidator(0)])
    currently_out = models.IntegerField(default=0, validators=[MinValueValidator(0)])

    @property
    def dynamic_qr_url(self):
        """Returns the absolute URL for the dynamic QR code generation."""
        from django.urls import reverse
        from django.conf import settings
        path = reverse('books:generate_qr', args=[self.id])
        domain = getattr(settings, 'RENDER_EXTERNAL_HOSTNAME', None)
        if domain:
            return f"https://{domain}{path}"
        # Fallback for development (might be relative or localhost)
        return path

    def __str__(self):
        return f"{self.title} by {self.author}"

    def save(self, *args, **kwargs):
        # Check if this is a new book (not updating existing)
        is_new = self.pk is None

        # Ensure ISBN exists
        if not self.isbn:
            self.isbn = str(uuid.uuid4())[:13]  # Generate a unique ISBN if not provided

        # Ensure available_copies within bounds
        if self.available_copies is None:
            self.available_copies = self.total_copies
        self.available_copies = max(0, min(self.available_copies, self.total_copies))

        # Calculate currently_out
        self.currently_out = self.total_copies - self.available_copies

        # Only auto-adjust status when book is not marked lost/damaged
        if self.status in ('AVAILABLE', 'ISSUED'):
            if self.available_copies > 0:
                self.status = 'AVAILABLE'
            else:
                self.status = 'ISSUED'

        super().save(*args, **kwargs)

    class Meta:
        ordering = ['title']

# Transaction Model
class Transaction(models.Model):
    TRANSACTION_TYPES = [
        ('ISSUE', 'Issue'),
        ('RETURN', 'Return'),
        ('RENEW', 'Renew'),
    ]

    book = models.ForeignKey(Book, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    transaction_type = models.CharField(max_length=10, choices=TRANSACTION_TYPES)
    issue_date = models.DateField(auto_now_add=True)
    due_date = models.DateField()
    return_date = models.DateField(null=True, blank=True)
    admin_notes = models.TextField(blank=True)
    condition_notes = models.TextField(blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_transactions')
    renewed_count = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.transaction_type}: {self.book.title} to {self.user.username}"

    def is_overdue(self):
        return self.return_date is None and timezone.now().date() > self.due_date

    @property
    def is_active(self):
        return self.return_date is None

    @classmethod
    def get_active_count_for_user(cls, user):
        """Get count of active (unreturned) books for a user"""
        return cls.objects.filter(user=user, return_date__isnull=True, transaction_type='ISSUE').count()

    @classmethod
    def user_has_overdue_books(cls, user):
        """Check if user has any overdue books"""
        return cls.objects.filter(
            user=user,
            return_date__isnull=True,
            transaction_type='ISSUE',
            due_date__lt=timezone.now().date()
        ).exists()

    @classmethod
    def user_has_book(cls, user, book):
        """Check if user currently has the specified book issued"""
        return cls.objects.filter(
            user=user,
            book=book,
            return_date__isnull=True,
            transaction_type='ISSUE'
        ).exists()

    def clean(self):
        from django.core.exceptions import ValidationError
        # For validation purposes, use current date if issue_date is not set (for new transactions)
        effective_issue_date = self.issue_date if self.issue_date else timezone.now().date()

        if not self.due_date:
            raise ValidationError("Due date is required.")
        if self.due_date <= effective_issue_date:
            raise ValidationError("Due date must be after issue date.")
        if self.return_date and self.return_date < effective_issue_date:
            raise ValidationError("Return date cannot be before issue date.")

    class Meta:
        ordering = ['-issue_date']

# Reading Log Model
class ReadingLog(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    book = models.ForeignKey(Book, on_delete=models.CASCADE)
    log_date = models.DateField(default=timezone.now)
    read_today = models.BooleanField(default=False)
    pages_read = models.IntegerField(default=0)
    minutes_read = models.IntegerField(default=0)
    notes = models.TextField(blank=True)
    progress = models.IntegerField(default=0, validators=[MinValueValidator(0), MaxValueValidator(100)])  # Percentage 0-100

    def __str__(self):
        return f"{self.user.username} - {self.book.title} - {self.log_date}"

    def save(self, *args, **kwargs):
        # Validate that user has the book issued before allowing reading log
        if not Transaction.user_has_book(self.user, self.book):
            from django.core.exceptions import ValidationError
            raise ValidationError(f"Cannot log reading for '{self.book.title}': You do not currently have this book issued.")
        super().save(*args, **kwargs)

    class Meta:
        unique_together = ['user', 'book', 'log_date']
        ordering = ['-log_date']

# Book Request Model
class BookRequest(models.Model):
    REQUEST_TYPES = [
        ('WAITLIST', 'Join Waitlist'),
        ('PURCHASE', 'Suggest Purchase'),
    ]

    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    book = models.ForeignKey(Book, on_delete=models.CASCADE, null=True, blank=True)
    request_type = models.CharField(max_length=10, choices=REQUEST_TYPES)
    title = models.CharField(max_length=200, blank=True)  # For purchase requests
    author = models.CharField(max_length=100, blank=True)
    reason = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    priority = models.IntegerField(default=1)
    created_date = models.DateTimeField(auto_now_add=True)
    fulfilled_date = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        if self.request_type == 'WAITLIST':
            return f"Waitlist: {self.book.title} by {self.user.username}"
        else:
            return f"Purchase: {self.title} by {self.author} - {self.user.username}"

    def save(self, *args, **kwargs):
        from core.utils import get_club_setting
        from django.core.exceptions import ValidationError
        from django.utils import timezone
        from datetime import timedelta

        # Check for duplicate pending requests
        if self.request_type == 'WAITLIST' and self.book:
            existing = BookRequest.objects.filter(
                user=self.user,
                book=self.book,
                request_type='WAITLIST',
                status='PENDING'
            ).exclude(pk=self.pk)
            if existing.exists():
                raise ValidationError("You already have a pending waitlist request for this book.")

        elif self.request_type == 'PURCHASE':
            existing = BookRequest.objects.filter(
                user=self.user,
                title__iexact=self.title,
                author__iexact=self.author,
                request_type='PURCHASE',
                status='PENDING'
            ).exclude(pk=self.pk)
            if existing.exists():
                raise ValidationError("You already have a pending purchase request for this book.")

        # Check user request limits
        max_requests = int(get_club_setting('MAX_REQUESTS_PER_USER', 10))
        user_pending_requests = BookRequest.objects.filter(
            user=self.user,
            status='PENDING'
        ).exclude(pk=self.pk).count()

        if user_pending_requests >= max_requests:
            raise ValidationError(f"You have reached the maximum limit of {max_requests} pending requests.")

        # Check cooldown period
        cooldown_hours = int(get_club_setting('REQUEST_COOLDOWN_HOURS', 24))
        if cooldown_hours > 0:
            cooldown_start = timezone.now() - timedelta(hours=cooldown_hours)
            recent_requests = BookRequest.objects.filter(
                user=self.user,
                created_date__gte=cooldown_start
            ).exclude(pk=self.pk).count()

            if recent_requests > 0:
                raise ValidationError(f"You must wait {cooldown_hours} hours between requests.")

        super().save(*args, **kwargs)

    class Meta:
        ordering = ['-created_date']

# Club Settings Model
class ClubSettings(models.Model):
    setting_key = models.CharField(max_length=50, unique=True)
    setting_value = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.setting_key}: {self.setting_value}"

    class Meta:
        verbose_name = "Club Setting"
        verbose_name_plural = "Club Settings"

    @classmethod
    def get_default_settings(cls):
        """Returns default settings for the club"""
        return {
            'MAX_ACTIVE_BOOKS_PER_USER': '5',
            'MAX_RENEWALS_PER_LOAN': '2',
            'RENEWAL_PERIOD_DAYS': '7',
            'LOAN_PERIOD_DAYS': '14',
            'OVERDUE_FINE_PER_DAY': '0.50',
            'MAX_REQUESTS_PER_USER': '10',
            'REQUEST_COOLDOWN_HOURS': '24',
        }
