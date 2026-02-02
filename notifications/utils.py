import uuid
from datetime import timedelta
from django.core.mail import send_mail, EmailMessage
from django.template.loader import render_to_string
from django.conf import settings
from django.utils import timezone
from core.models import Transaction, Book
from .models import UserNotification, EmailLog


def send_welcome_email(user):
    """Send a welcome email to a user with enhanced HTML template.
    If user.email is empty, do nothing.
    """
    if not user.email:
        return False

    subject = 'Welcome to Book Club - Your Reading Journey Begins!'
    tracking_id = str(uuid.uuid4())

    # Get some sample books for recommendations
    sample_books = Book.objects.filter(status='AVAILABLE')[:3]

    context = {
        'user': user,
        'sample_books': sample_books,
        'tracking_id': tracking_id,
        'unsubscribe_url': f"/users/unsubscribe/{user.id}/",
        'preferences_url': f"/users/settings/",
        'tracking_pixel': f"/email/track/{tracking_id}/open/"
    }

    html_message = render_to_string('email/welcome_email.html', context)

    # Create EmailLog entry with enhanced tracking
    email_log = EmailLog.objects.create(
        user=user,
        email_type='WELCOME',
        subject=subject,
        recipient=user.email,
        email_content=html_message,
        campaign_id=tracking_id
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


def send_overdue_alerts():
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
            email_content=html_message
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


def send_overdue_alerts_for_qs(transaction_qs):
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
            email_content=html_message
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
