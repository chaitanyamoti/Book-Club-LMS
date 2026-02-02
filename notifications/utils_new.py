import uuid
from datetime import timedelta
from django.core.mail import send_mail, EmailMessage
from django.template.loader import render_to_string
from django.conf import settings
from django.utils import timezone
from core.models import Transaction, Book, ReadingLog, UserProfile # Add UserProfile and ReadingLog
from .models import UserNotification, EmailLog
import random # Import random for A/B testing


def get_ab_test_variant(variants=['A', 'B']):
    """Randomly selects an A/B test variant."""
    return random.choice(variants)


def send_welcome_email(user, ab_test_variant=None):
    """Send a welcome email to a user with enhanced HTML template.
    If user.email is empty, do nothing.
    """
    if not user.email:
        return False

    subject = 'Welcome to Book Club - Your Reading Journey Begins!'
    log_uuid = uuid.uuid4() # Generate UUID for this email log

    # Get some sample books for recommendations
    sample_books = Book.objects.filter(status='AVAILABLE')[:3]

    context = {
        'user': user,
        'sample_books': sample_books,
        'unsubscribe_url': f"/users/unsubscribe/{user.id}/",
        'preferences_url': f"/users/settings/",
        'tracking_pixel': f"/notifications/track-open/{log_uuid}/" # Use the correct URL and log_uuid
    }

    html_message = render_to_string('email/welcome_email.html', context)

    # Create EmailLog entry with enhanced tracking
    email_log = EmailLog.objects.create(
        uuid=log_uuid, # Assign the generated UUID
        user=user,
        email_type='WELCOME',
        subject=subject,
        recipient=user.email,
        email_content=html_message,
        campaign_id=str(log_uuid), # Optionally keep campaign_id as string representation of uuid
        ab_test_variant=ab_test_variant
    )

    try:
        # Send HTML-only email
        email = EmailMessage(
            subject,
            html_message,
            settings.DEFAULT_FROM_EMAIL if hasattr(settings, 'DEFAULT_FROM_EMAIL') else 'noreply@bookclub.com',
            [user.email],
        )
        email.content_subtype = 'html'  # Set content type to HTML
        email.send()

        # Update log on success
        email_log.status = 'SENT'
        email_log.sent_at = timezone.now()
        email_log.save()

        # Create in-app notification
        UserNotification.objects.create(
            user=user,
            message="Welcome to Book Club! Check your email for getting started tips.",
            type='INFO',
            link_url='/dashboard/'
        )

        return True
    except Exception as e:
        # Update log on failure
        email_log.status = 'FAILED'
        email_log.error_message = str(e)
        email_log.save()
        return False


def send_overdue_alerts(ab_test_variant=None):
    """Find overdue transactions and send alert emails to affected users.
    Returns the number of emails sent.
    """
    today = timezone.now().date()
    overdue_qs = Transaction.objects.filter(return_date__isnull=True, due_date__lt=today).select_related('user', 'book')

    # Group transactions by user
    users_map = {}
    for tx in overdue_qs:
        users_map.setdefault(tx.user, []).append(tx)

    sent = 0
    for user, transactions in users_map.items():
        if not user.email:
            continue

        # Prepare transaction info for template
        overdue_transactions = []
        for tx in transactions:
            days_overdue = (today - tx.due_date).days
            overdue_transactions.append({
                'book': tx.book,
                'due_date': tx.due_date,
                'days_overdue': days_overdue,
                'transaction': tx,
            })

        subject = f"Overdue Book Alert - {len(overdue_transactions)} book(s)"
        context = {
            'user': user,
            'overdue_transactions': overdue_transactions,
            'club_name': getattr(settings, 'SITE_NAME', 'Book Club')
        }
        html_message = render_to_string('email/overdue_warning.html', context)

        # Create EmailLog entry
        email_log = EmailLog.objects.create(
            user=user,
            email_type='OVERDUE',
            subject=subject,
            recipient=user.email,
            email_content=html_message,
            ab_test_variant=ab_test_variant
        )

        try:
            # Send HTML-only email
            email = EmailMessage(
                subject,
                html_message,
                settings.DEFAULT_FROM_EMAIL if hasattr(settings, 'DEFAULT_FROM_EMAIL') else None,
                [user.email],
            )
            email.content_subtype = 'html'
            email.send()

            # Update log on success
            email_log.status = 'SENT'
            email_log.sent_at = timezone.now()
            email_log.save()

            sent += 1

            # Create in-app UserNotification
            UserNotification.objects.create(
                user=user,
                message=f"You have {len(overdue_transactions)} overdue book(s). Please return them immediately.",
                type='OVERDUE',
                link_url='/transactions/'
            )
        except Exception as e:
            # Update log on failure
            email_log.status = 'FAILED'
            email_log.error_message = str(e)
            email_log.save()

    return sent


def send_overdue_alerts_for_qs(transaction_qs, ab_test_variant=None):
    """Send overdue alerts for a given queryset of Transaction objects and return number of emails sent."""
    today = timezone.now().date()
    overdue_qs = transaction_qs.select_related('user', 'book')

    # Group transactions by user
    users_map = {}
    for tx in overdue_qs:
        users_map.setdefault(tx.user, []).append(tx)

    sent = 0
    for user, transactions in users_map.items():
        if not user.email:
            continue

        overdue_transactions = []
        for tx in transactions:
            days_overdue = (today - tx.due_date).days if tx.due_date else None
            overdue_transactions.append({
                'book': tx.book,
                'due_date': tx.due_date,
                'days_overdue': days_overdue,
                'transaction': tx,
            })

        subject = f"Overdue Book Alert - {len(overdue_transactions)} book(s)"
        context = {
            'user': user,
            'overdue_transactions': overdue_transactions,
            'club_name': getattr(settings, 'SITE_NAME', 'Book Club')
        }
        html_message = render_to_string('email/overdue_warning.html', context)

        # Create EmailLog entry
        email_log = EmailLog.objects.create(
            user=user,
            email_type='OVERDUE',
            subject=subject,
            recipient=user.email,
            email_content=html_message,
            ab_test_variant=ab_test_variant
        )

        try:
            # Send HTML-only email
            email = EmailMessage(
                subject,
                html_message,
                settings.DEFAULT_FROM_EMAIL if hasattr(settings, 'DEFAULT_FROM_EMAIL') else None,
                [user.email],
            )
            email.content_subtype = 'html'
            email.send()

            # Update log on success
            email_log.status = 'SENT'
            email_log.sent_at = timezone.now()
            email_log.save()

            sent += 1

            # Create in-app UserNotification
            UserNotification.objects.create(
                user=user,
                message=f"You have {len(overdue_transactions)} overdue book(s). Please return them immediately.",
                type='OVERDUE',
                link_url='/transactions/'
            )
        except Exception as e:
            # Update log on failure
            email_log.status = 'FAILED'
            email_log.error_message = str(e)
            email_log.save()

    return sent


def send_book_issued_email(transaction, ab_test_variant=None):
    """Send confirmation email when a book is issued to a user."""
    if not transaction.user.email:
        return False

    days_until_due = (transaction.due_date - timezone.now().date()).days

    # Get recommended books (simple logic: same genre, different books)
    recommended_books = []
    if transaction.book.genre:
        recommended_books = Book.objects.filter(
            genre=transaction.book.genre,
            status='AVAILABLE'
        ).exclude(id=transaction.book.id)[:2]

    subject = f"Your Book is Ready - {transaction.book.title}"
    log_uuid = uuid.uuid4() # Generate UUID for this email log

    context = {
        'transaction': transaction,
        'days_until_due': days_until_due,
        'recommended_books': recommended_books,
        'unsubscribe_url': f"/users/unsubscribe/{transaction.user.id}/",
        'preferences_url': f"/users/settings/",
        'tracking_pixel': f"/notifications/track-open/{log_uuid}/",
        'qr_code_url': transaction.book.qr_code.url if transaction.book.qr_code else None
    }

    html_message = render_to_string('email/book_issued.html', context)

    # Create EmailLog entry
    email_log = EmailLog.objects.create(
        uuid=log_uuid, # Assign the generated UUID
        user=transaction.user,
        email_type='BOOK_ISSUED',
        subject=subject,
        recipient=transaction.user.email,
        email_content=html_message,
        campaign_id=str(log_uuid), # Optionally keep campaign_id as string representation of uuid
        ab_test_variant=ab_test_variant
    )

    try:
        # Send HTML-only email
        email = EmailMessage(
            subject,
            html_message,
            settings.DEFAULT_FROM_EMAIL if hasattr(settings, 'DEFAULT_FROM_EMAIL') else 'noreply@bookclub.com',
            [transaction.user.email],
        )
        email.content_subtype = 'html'
        email.send()

        # Update log on success
        email_log.status = 'SENT'
        email_log.sent_at = timezone.now()
        email_log.save()

        # Create in-app notification
        UserNotification.objects.create(
            user=transaction.user,
            message=f"Great news! '{transaction.book.title}' is ready for you. Check your email for details.",
            type='INFO',
            link_url=f'/books/{transaction.book.id}/'
        )

        return True
    except Exception as e:
        # Update log on failure
        email_log.status = 'FAILED'
        email_log.error_message = str(e)
        email_log.save()
        return False


def send_due_reminder_email(transaction, reminder_type='gentle', ab_test_variant=None):
    """Send due date reminder email for a transaction."""
    if not transaction.user.email:
        return False

    today = timezone.now().date()
    days_remaining = (transaction.due_date - today).days

    log_uuid = uuid.uuid4() # Generate UUID for this email log

    context = {
        'transaction': transaction,
        'days_remaining': days_remaining,
        'reminder_type': reminder_type,
        'unsubscribe_url': f"/users/unsubscribe/{transaction.user.id}/",
        'preferences_url': f"/users/settings/",
        'tracking_pixel': f"/notifications/track-open/{log_uuid}/" # Use the correct URL and log_uuid
    }

    # Customize subject and styling based on reminder type
    if days_remaining > 0:
        subject = f"Book Due Soon - {transaction.book.title}"
    elif days_remaining == 0:
        subject = f"Book Due Today - {transaction.book.title}"
    else:
        subject = f"Overdue Book Notice - {transaction.book.title}"

    html_message = render_to_string('email/due_reminder.html', context)

    # Create EmailLog entry
    email_log = EmailLog.objects.create(
        uuid=log_uuid, # Assign the generated UUID
        user=transaction.user,
        email_type='DUE_REMINDER',
        subject=subject,
        recipient=transaction.user.email,
        email_content=html_message,
        campaign_id=str(log_uuid), # Optionally keep campaign_id as string representation of uuid
        ab_test_variant=ab_test_variant
    )

    try:
        # Send HTML-only email
        email = EmailMessage(
            subject,
            html_message,
            settings.DEFAULT_FROM_EMAIL if hasattr(settings, 'DEFAULT_FROM_EMAIL') else 'noreply@bookclub.com',
            [transaction.user.email],
        )
        email.content_subtype = 'html'
        email.send()

        # Update log on success
        email_log.status = 'SENT'
        email_log.sent_at = timezone.now()
        email_log.save()

        # Create in-app notification
        if days_remaining > 0:
            message = f"'{transaction.book.title}' is due in {days_remaining} days."
        elif days_remaining == 0:
            message = f"'{transaction.book.title}' is due today!"
        else:
            message = f"'{transaction.book.title}' is {abs(days_remaining)} days overdue."

        UserNotification.objects.create(
            user=transaction.user,
            message=message,
            type='WARNING' if days_remaining <= 0 else 'INFO',
            link_url=f'/transactions/{transaction.id}/return/'
        )

        return True
    except Exception as e:
        # Update log on failure
        email_log.status = 'FAILED'
        email_log.error_message = str(e)
        email_log.save()
        return False


def send_bulk_due_reminders(ab_test_variant=None):
    """Send due date reminders for all transactions approaching due dates.
    Returns number of emails sent.
    """
    today = timezone.now().date()
    sent = 0

    # Define reminder schedules
    reminder_schedules = [
        (1, 'final_reminder'),  # 1 day before due
        (3, 'gentle_reminder'), # 3 days before due
        (7, 'early_reminder'),  # 7 days before due
    ]

    for days_before, reminder_type in reminder_schedules:
        target_date = today + timedelta(days=days_before)
        transactions = Transaction.objects.filter(
            due_date=target_date,
            return_date__isnull=True
        ).select_related('user', 'book')

        for transaction in transactions:
            if send_due_reminder_email(transaction, reminder_type, ab_test_variant):
                sent += 1

    # Also send overdue reminders
    overdue_transactions = Transaction.objects.filter(
        due_date__lt=today,
        return_date__isnull=True
    ).select_related('user', 'book')

    for transaction in overdue_transactions:
        if send_due_reminder_email(transaction, 'overdue', ab_test_variant):
            sent += 1

    return sent


def send_reading_streak_email(user, streak_days, ab_test_variant=None):
    """Send an email to a user when they achieve a reading streak milestone."""
    if not user.email:
        return False

    log_uuid = uuid.uuid4()

    context = {
        'user': user,
        'streak_days': streak_days,
        'unsubscribe_url': f"/users/unsubscribe/{user.id}/",
        'preferences_url': f"/users/settings/",
        'tracking_pixel': f"/notifications/track-open/{log_uuid}/"
    }

    subject = f"🎉 Congratulations on Your {streak_days}-Day Reading Streak!"
    html_message = render_to_string('email/reading/streak_milestone.html', context)

    email_log = EmailLog.objects.create(
        uuid=log_uuid,
        user=user,
        email_type='READING_STREAK',
        subject=subject,
        recipient=user.email,
        email_content=html_message,
        campaign_id=str(log_uuid),
        ab_test_variant=ab_test_variant
    )

    try:
        email = EmailMessage(
            subject,
            html_message,
            settings.DEFAULT_FROM_EMAIL if hasattr(settings, 'DEFAULT_FROM_EMAIL') else 'noreply@bookclub.com',
            [user.email],
        )
        email.content_subtype = 'html'
        email.send()

        email_log.status = 'SENT'
        email_log.sent_at = timezone.now()
        email_log.save()

        UserNotification.objects.create(
            user=user,
            message=f"Congratulations! You've achieved a {streak_days}-day reading streak!",
            type='INFO',
            link_url='/dashboard/'
        )
        return True
    except Exception as e:
        email_log.status = 'FAILED'
        email_log.error_message = str(e)
        email_log.save()
        return False


def send_monthly_reading_summary_email(user, ab_test_variant=None):
    """Sends a monthly reading summary email to the user."""
    if not user.email:
        return False

    log_uuid = uuid.uuid4()

    # Calculate dates for the previous month
    today = timezone.localdate()
    first_day_of_current_month = today.replace(day=1)
    last_day_of_previous_month = first_day_of_current_month - timedelta(days=1)
    first_day_of_previous_month = last_day_of_previous_month.replace(day=1)

    # Get reading logs for the previous month
    reading_logs = ReadingLog.objects.filter(
        user=user,
        log_date__range=(first_day_of_previous_month, last_day_of_previous_month)
    )

    # Calculate summary statistics
    books_read_ids = set()
    total_pages_read = 0
    total_minutes_read = 0
    books_read_list = [] # For displaying in email

    for log in reading_logs:
        books_read_ids.add(log.book.id)
        total_pages_read += log.pages_read
        total_minutes_read += log.minutes_read
        if log.book not in books_read_list: # Avoid duplicates for display
            books_read_list.append(log.book)

    books_completed = len(books_read_ids)

    context = {
        'user': user,
        'month_name': first_day_of_previous_month.strftime('%B'),
        'year': first_day_of_previous_month.year,
        'books_completed': books_completed,
        'total_pages_read': total_pages_read,
        'total_minutes_read': total_minutes_read,
        'books_read_list': books_read_list,
        'unsubscribe_url': f"/users/unsubscribe/{user.id}/",
        'preferences_url': f"/users/settings/",
        'tracking_pixel': f"/notifications/track-open/{log_uuid}/"
    }

    subject = f"Your Monthly Reading Summary - {first_day_of_previous_month.strftime('%B %Y')}"
    html_message = render_to_string('email/reading/monthly_summary.html', context)

    email_log = EmailLog.objects.create(
        uuid=log_uuid,
        user=user,
        email_type='MONTHLY_SUMMARY',
        subject=subject,
        recipient=user.email,
        email_content=html_message,
        campaign_id=str(log_uuid),
        ab_test_variant=ab_test_variant
    )

    try:
        email = EmailMessage(
            subject,
            html_message,
            settings.DEFAULT_FROM_EMAIL if hasattr(settings, 'DEFAULT_FROM_EMAIL') else 'noreply@bookclub.com',
            [user.email],
        )
        email.content_subtype = 'html'
        email.send()

        email_log.status = 'SENT'
        email_log.sent_at = timezone.now()
        email_log.save()

        UserNotification.objects.create(
            user=user,
            message=f"Here's your reading summary for {first_day_of_previous_month.strftime('%B')}!",
            type='INFO',
            link_url='/dashboard/' # Link to a dashboard with stats
        )
        return True
    except Exception as e:
        email_log.status = 'FAILED'
        email_log.error_message = str(e)
        email_log.save()
        return False


def send_books_read_milestone_email(user, books_read_count, ab_test_variant=None):
    """Send an email to a user when they achieve a books read milestone."""
    if not user.email:
        return False

    log_uuid = uuid.uuid4()

    context = {
        'user': user,
        'books_read_count': books_read_count,
        'unsubscribe_url': f"/users/unsubscribe/{user.id}/",
        'preferences_url': f"/users/settings/",
        'tracking_pixel': f"/notifications/track-open/{log_uuid}/"
    }

    subject = f"🏆 You've Read {books_read_count} Books!"
    html_message = render_to_string('email/reading/books_read_milestone.html', context)

    email_log = EmailLog.objects.create(
        uuid=log_uuid,
        user=user,
        email_type='BOOKS_READ_MILESTONE',
        subject=subject,
        recipient=user.email,
        email_content=html_message,
        campaign_id=str(log_uuid),
        ab_test_variant=ab_test_variant
    )

    try:
        email = EmailMessage(
            subject,
            html_message,
            settings.DEFAULT_FROM_EMAIL if hasattr(settings, 'DEFAULT_FROM_EMAIL') else 'noreply@bookclub.com',
            [user.email],
        )
        email.content_subtype = 'html'
        email.send()

        email_log.status = 'SENT'
        email_log.sent_at = timezone.now()
        email_log.save()

        UserNotification.objects.create(
            user=user,
            message=f"Congratulations! You've read {books_read_count} books!",
            type='INFO',
            link_url='/dashboard/'
        )
        return True
    except Exception as e:
        email_log.status = 'FAILED'
        email_log.error_message = str(e)
        email_log.save()
        return False


def send_challenge_invitation_email(user, challenge, ab_test_variant=None):
    """Sends an email inviting a user to a reading challenge."""
    if not user.email:
        return False

    log_uuid = uuid.uuid4()
    
    # Get the base URL for the site for correct links in email
    site_url = getattr(settings, 'SITE_URL', 'http://localhost:8000')

    context = {
        'user': user,
        'challenge': challenge,
        'site_url': site_url,
        'unsubscribe_url': f"{site_url}/users/unsubscribe/{user.id}/",
        'preferences_url': f"{site_url}/users/settings/",
        'tracking_pixel': f"/notifications/track-open/{log_uuid}/"
    }

    subject = f"🚀 Join Our New Reading Challenge: {challenge.name}!"
    html_message = render_to_string('email/reading/challenge_invitation.html', context)

    email_log = EmailLog.objects.create(
        uuid=log_uuid,
        user=user,
        email_type='CHALLENGE_INVITATION',
        subject=subject,
        recipient=user.email,
        email_content=html_message,
        campaign_id=str(log_uuid),
        ab_test_variant=ab_test_variant
    )

    try:
        email = EmailMessage(
            subject,
            html_message,
            settings.DEFAULT_FROM_EMAIL if hasattr(settings, 'DEFAULT_FROM_EMAIL') else 'noreply@bookclub.com',
            [user.email],
        )
        email.content_subtype = 'html'
        email.send()

        email_log.status = 'SENT'
        email_log.sent_at = timezone.now()
        email_log.save()

        UserNotification.objects.create(
            user=user,
            message=f"You've been invited to join the '{challenge.name}' reading challenge!",
            type='INFO',
            link_url=f"/reading/challenges/{challenge.id}/"
        )
        return True
    except Exception as e:
        email_log.status = 'FAILED'
        email_log.error_message = str(e)
        email_log.save()
        return False


def send_challenge_progress_email(user_challenge, ab_test_variant=None):
    """Sends an email updating a user on their progress in a reading challenge."""
    user = user_challenge.user
    challenge = user_challenge.challenge

    if not user.email:
        return False

    log_uuid = uuid.uuid4()
    
    site_url = getattr(settings, 'SITE_URL', 'http://localhost:8000')

    context = {
        'user': user,
        'challenge': challenge,
        'user_challenge': user_challenge,
        'site_url': site_url,
        'unsubscribe_url': f"{site_url}/users/unsubscribe/{user.id}/",
        'preferences_url': f"{site_url}/users/settings/",
        'tracking_pixel': f"/notifications/track-open/{log_uuid}/"
    }

    subject = f"Reading Challenge Update: {challenge.name}"
    html_message = render_to_string('email/reading/challenge_progress.html', context)

    email_log = EmailLog.objects.create(
        uuid=log_uuid,
        user=user,
        email_type='CHALLENGE_PROGRESS',
        subject=subject,
        recipient=user.email,
        email_content=html_message,
        campaign_id=str(log_uuid),
        ab_test_variant=ab_test_variant
    )

    try:
        email = EmailMessage(
            subject,
            html_message,
            settings.DEFAULT_FROM_EMAIL if hasattr(settings, 'DEFAULT_FROM_EMAIL') else 'noreply@bookclub.com',
            [user.email],
        )
        email.content_subtype = 'html'
        email.send()

        email_log.status = 'SENT'
        email_log.sent_at = timezone.now()
        email_log.save()

        UserNotification.objects.create(
            user=user,
            message=f"Here's your progress update for the '{challenge.name}' challenge!",
            type='INFO',
            link_url=f"/reading/challenges/{challenge.id}/"
        )
        return True
    except Exception as e:
        email_log.status = 'FAILED'
        email_log.error_message = str(e)
        email_log.save()
        return False


def send_new_book_alert_email(book, ab_test_variant=None):
    """Sends an email to all users about a newly added book."""
    from django.contrib.auth.models import User
    from notifications.models import EmailPreference

    log_uuid = uuid.uuid4()
    site_url = getattr(settings, 'SITE_URL', 'http://localhost:8000')

    # Get all users who prefer to receive new announcements
    # This assumes EmailPreference model is linked to User and has community_emails field
    users_to_notify = User.objects.filter(
        email__isnull=False,
        email__icontains='@',
        emailpreference__community_emails=True # Check user preference
    )

    sent_count = 0
    for user in users_to_notify:
        context = {
            'user': user,
            'book': book,
            'site_url': site_url,
            'unsubscribe_url': f"{site_url}/users/unsubscribe/{user.id}/",
            'preferences_url': f"{site_url}/users/settings/",
            'tracking_pixel': f"/notifications/track-open/{log_uuid}/" # Use the same log_uuid for all recipients for now
        }

        subject = f"✨ New Book Alert: \"{book.title}\"!"
        html_message = render_to_string('email/community/new_book_alert.html', context)

        email_log = EmailLog.objects.create(
            uuid=uuid.uuid4(), # Generate unique UUID for each email log
            user=user,
            email_type='NEW_BOOK_ALERT',
            subject=subject,
            recipient=user.email,
            email_content=html_message,
            campaign_id=str(log_uuid), # Campaign ID can be shared for all emails in a batch
            ab_test_variant=ab_test_variant
        )

        try:
            email = EmailMessage(
                subject,
                html_message,
                settings.DEFAULT_FROM_EMAIL if hasattr(settings, 'DEFAULT_FROM_EMAIL') else 'noreply@bookclub.com',
                [user.email],
            )
            email.content_subtype = 'html'
            email.send()

            email_log.status = 'SENT'
            email_log.sent_at = timezone.now()
            email_log.save()
            sent_count += 1

        except Exception as e:
            email_log.status = 'FAILED'
            email_log.error_message = str(e)
            email_log.save()
            
    return sent_count


def send_reading_group_invitation_email(user, group, ab_test_variant=None):
    """Sends an email inviting a user to a reading group."""
    if not user.email:
        return False

    log_uuid = uuid.uuid4()
    site_url = getattr(settings, 'SITE_URL', 'http://localhost:8000')

    context = {
        'user': user,
        'group': group,
        'site_url': site_url,
        'unsubscribe_url': f"{site_url}/users/unsubscribe/{user.id}/",
        'preferences_url': f"{site_url}/users/settings/",
        'tracking_pixel': f"/notifications/track-open/{log_uuid}/"
    }

    subject = f"👥 You're Invited to Join the Reading Group: {group.name}!"
    html_message = render_to_string('email/community/reading_group_invitation.html', context)

    email_log = EmailLog.objects.create(
        uuid=log_uuid,
        user=user,
        email_type='READING_GROUP_INVITATION',
        subject=subject,
        recipient=user.email,
        email_content=html_message,
        campaign_id=str(log_uuid),
        ab_test_variant=ab_test_variant
    )

    try:
        email = EmailMessage(
            subject,
            html_message,
            settings.DEFAULT_FROM_EMAIL if hasattr(settings, 'DEFAULT_FROM_EMAIL') else 'noreply@bookclub.com',
            [user.email],
        )
        email.content_subtype = 'html'
        email.send()

        email_log.status = 'SENT'
        email_log.sent_at = timezone.now()
        email_log.save()

        UserNotification.objects.create(
            user=user,
            message=f"You've been invited to the '{group.name}' reading group!",
            type='INFO',
            link_url=f"/reading/groups/{group.id}/"
        )
        return True
    except Exception as e:
        email_log.status = 'FAILED'
        email_log.error_message = str(e)
        email_log.save()
        return False


def send_monthly_newsletter_email(ab_test_variant=None):
    """Sends a monthly newsletter to all users who have opted in."""
    from django.contrib.auth.models import User
    from notifications.models import EmailPreference
    from core.models import Book, UserProfile, Transaction
    from django.db.models import Count # For annotations

    site_url = getattr(settings, 'SITE_URL', 'http://localhost:8000')
    log_uuid_campaign = uuid.uuid4() # Campaign ID for this entire newsletter send

    today = timezone.localdate()
    first_day_of_current_month = today.replace(day=1)
    last_day_of_previous_month = first_day_of_current_month - timedelta(days=1)
    first_day_of_previous_month = last_day_of_previous_month.replace(day=1)

    month_name = first_day_of_previous_month.strftime('%B')
    year = first_day_of_previous_month.year

    # --- Gather Newsletter Content ---

    # 1. Top books (e.g., most issued last month)
    top_books = Book.objects.filter(
        transaction__issue_date__range=(first_day_of_previous_month, last_day_of_previous_month)
    ).annotate(issue_count=Count('transaction')).order_by('-issue_count')[:3]

    # 2. Member Spotlight (randomly pick an active user with some reading activity)
    spotlight_member = UserProfile.objects.filter(
        total_books_read__gt=0, is_active=True
    ).order_by('?').first() # '?' for random order

    # 3. Upcoming Events/Challenges (placeholder for now)
    upcoming_events = [
        {'name': 'Spring Reading Challenge', 'date': today + timedelta(days=15), 'description': 'Dive into fantasy novels!'},
        {'name': 'Author Talk: Jane Doe', 'date': today + timedelta(days=25), 'description': 'Virtual Q&A with best-selling author.'},
    ]

    # --- Send to Users ---
    users_to_notify = User.objects.filter(
        email__isnull=False,
        email__icontains='@',
        emailpreference__email_weekly_digest=True # Assuming monthly newsletter falls under this preference
    )

    sent_count = 0
    for user in users_to_notify:
        context = {
            'user': user,
            'month_name': month_name,
            'year': year,
            'top_books': top_books,
            'spotlight_member': spotlight_member,
            'upcoming_events': upcoming_events,
            'site_url': site_url,
            'unsubscribe_url': f"{site_url}/users/unsubscribe/{user.id}/",
            'preferences_url': f"{site_url}/users/settings/",
            'tracking_pixel': f"/notifications/track-open/{log_uuid_campaign}/"
        }

        subject = f"📚 Your Monthly Book Club Newsletter - {month_name} {year}"
        html_message = render_to_string('email/community/monthly_newsletter.html', context)

        email_log = EmailLog.objects.create(
            uuid=uuid.uuid4(), # Unique UUID for each email instance
            user=user,
            email_type='MONTHLY_NEWSLETTER',
            subject=subject,
            recipient=user.email,
            email_content=html_message,
            campaign_id=str(log_uuid_campaign),
            ab_test_variant=ab_test_variant
        )

        try:
            email = EmailMessage(
                subject,
                html_message,
                settings.DEFAULT_FROM_EMAIL if hasattr(settings, 'DEFAULT_FROM_EMAIL') else 'noreply@bookclub.com',
                [user.email],
            )
            email.content_subtype = 'html'
            email.send()

            email_log.status = 'SENT'
            email_log.sent_at = timezone.now()
            email_log.save()
            sent_count += 1
        except Exception as e:
            email_log.status = 'FAILED'
            email_log.error_message = str(e)
            email_log.save()
            
    return sent_count


def send_book_returned_email(transaction, ab_test_variant=None):
    """Send confirmation email when a book is returned by a user."""
    if not transaction.user.email:
        return False

    log_uuid = uuid.uuid4()

    # Placeholder for reading stats and recommendations - to be implemented
    reading_stats = {
        'total_books_read': transaction.user.transaction_set.filter(transaction_type='RETURN', return_date__isnull=False).count(),
        # Add more sophisticated stats here later
    }
    recommended_books = Book.objects.filter(status='AVAILABLE').order_by('?')[:2] # Simple random recommendation

    context = {
        'user': transaction.user,
        'transaction': transaction,
        'reading_stats': reading_stats,
        'recommended_books': recommended_books,
        'unsubscribe_url': f"/users/unsubscribe/{transaction.user.id}/",
        'preferences_url': f"/users/settings/",
        'tracking_pixel': f"/notifications/track-open/{log_uuid}/"
    }

    subject = f"Thank You for Returning '{transaction.book.title}'!"
    html_message = render_to_string('email/transactions/book_returned.html', context)

    email_log = EmailLog.objects.create(
        uuid=log_uuid,
        user=transaction.user,
        email_type='BOOK_RETURNED',
        subject=subject,
        recipient=transaction.user.email,
        email_content=html_message,
        campaign_id=str(log_uuid),
        ab_test_variant=ab_test_variant
    )

    try:
        email = EmailMessage(
            subject,
            html_message,
            settings.DEFAULT_FROM_EMAIL if hasattr(settings, 'DEFAULT_FROM_EMAIL') else 'noreply@bookclub.com',
            [transaction.user.email],
        )
        email.content_subtype = 'html'
        email.send()

        email_log.status = 'SENT'
        email_log.sent_at = timezone.now()
        email_log.save()

        UserNotification.objects.create(
            user=transaction.user,
            message=f"Thank you for returning '{transaction.book.title}'. We hope you enjoyed it!",
            type='INFO',
            link_url='/dashboard/'
        )
        return True
    except Exception as e:
        email_log.status = 'FAILED'
        email_log.error_message = str(e)
        email_log.save()
        return False


def optimize_send_times(user):
    """
    Placeholder to determine optimal email send times based on user behavior.
    To be implemented with more sophisticated logic analyzing past open times,
    click-throughs, and user activity patterns.
    """
    # For now, return a default time (e.g., now) or None if no specific optimization
    return timezone.now()
