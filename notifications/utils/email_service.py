"""
Enhanced email service for transaction lifecycle and engagement emails.
Handles template selection, preference checking, and tracking integration.
"""
import logging
from django.template.loader import render_to_string
from django.core.mail import EmailMessage
from django.utils import timezone
from django.conf import settings
from notifications.models import EmailLog, EmailPreference
from core.models import Book

logger = logging.getLogger(__name__)


class TransactionEmailService:
    """
    Service for sending transaction-related emails with enhanced features.
    """

    def send_book_issued_confirmation(self, transaction, recommended_books=None):
        """
        Send enhanced book issued confirmation email.

        Args:
            transaction: Transaction instance
            recommended_books: Optional list of recommended books
        """
        if not self._check_user_preferences(transaction.user, 'transaction_emails'):
            logger.info(f"User {transaction.user.username} has opted out of transaction emails")
            return False

        # Calculate days until due
        days_until_due = (transaction.due_date - timezone.now().date()).days

        context = {
            'transaction': transaction,
            'user': transaction.user,
            'days_until_due': days_until_due,
            'recommended_books': recommended_books or self._get_recommendations(transaction.user),
        }

        return self._send_transaction_email(
            user=transaction.user,
            template_name='email/book_issued.html',
            context=context,
            email_type='BOOK_ISSUED',
            campaign_id=f'transaction_{transaction.id}',
            subject=f"Your Book is Ready - {transaction.book.title}"
        )

    def send_return_confirmation(self, transaction, reading_stats=None, achievements=None):
        """
        Send enhanced book return confirmation email.

        Args:
            transaction: Transaction instance
            reading_stats: Optional reading statistics
            achievements: Optional list of achievements unlocked
        """
        if not self._check_user_preferences(transaction.user, 'transaction_emails'):
            logger.info(f"User {transaction.user.username} has opted out of transaction emails")
            return False

        context = {
            'user': transaction.user,
            'book': transaction.book,
            'return_date': timezone.now(),
            'condition_notes': getattr(transaction, 'condition_notes', ''),
            'reading_stats': reading_stats or self._get_reading_stats(transaction.user),
            'recommended_books': self._get_recommendations(transaction.user),
            'achievements': achievements or [],
        }

        return self._send_transaction_email(
            user=transaction.user,
            template_name='email/book_returned.html',
            context=context,
            email_type='BOOK_RETURNED',
            campaign_id=f'return_{transaction.id}',
            subject=f"📚 Book Returned Successfully - {transaction.book.title}"
        )

    def send_due_reminder(self, transaction, reminder_type='due_reminder', days_remaining=0):
        """
        Send due date reminder email.

        Args:
            transaction: Transaction instance
            reminder_type: Type of reminder (gentle, firm, final, etc.)
            days_remaining: Days until due date
        """
        if not self._check_user_preferences(transaction.user, 'transaction_emails'):
            logger.info(f"User {transaction.user.username} has opted out of transaction emails")
            return False

        context = {
            'transaction': transaction,
            'user': transaction.user,
            'days_remaining': days_remaining,
            'days_until_due': days_remaining,
            'reminder_type': reminder_type,
        }

        # Select appropriate template based on reminder type
        template_map = {
            'gentle_reminder': 'email/transactions/gentle_reminder.html',
            'firm_reminder': 'email/transactions/firm_reminder.html',
            'final_reminder': 'email/transactions/final_reminder.html',
            'overdue_warning': 'email/transactions/overdue_warning.html',
            'overdue_escalation': 'email/transactions/overdue_escalation.html',
        }

        template_name = template_map.get(reminder_type, 'email/due_reminder.html')

        # Get appropriate subject
        subject_map = {
            'gentle_reminder': f"Friendly reminder: {transaction.book.title} due soon",
            'firm_reminder': f"Important: {transaction.book.title} due tomorrow",
            'final_reminder': f"Final notice: {transaction.book.title} due today",
            'overdue_warning': f"Overdue: {transaction.book.title} needs to be returned",
            'overdue_escalation': f"Urgent: {transaction.book.title} is 7 days overdue",
        }

        subject = subject_map.get(reminder_type, f"Book reminder: {transaction.book.title}")

        return self._send_transaction_email(
            user=transaction.user,
            template_name=template_name,
            context=context,
            email_type=f'REMINDER_{reminder_type.upper()}',
            campaign_id=f'reminder_{transaction.id}_{reminder_type}',
            subject=subject
        )

    def _send_transaction_email(self, user, template_name, context, email_type, campaign_id, subject):
        """
        Core method to send transaction emails with logging and tracking.

        Args:
            user: User instance
            template_name: Template to use
            context: Template context
            email_type: Type of email for logging
            campaign_id: Campaign identifier for tracking
            subject: Email subject

        Returns:
            bool: Success status
        """
        try:
            # Render HTML content
            html_content = render_to_string(template_name, context)

            # Create email message
            email = EmailMessage(
                subject=subject,
                body=html_content,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[user.email],
            )
            email.content_subtype = 'html'

            # Send email
            sent_count = email.send()

            if sent_count > 0:
                # Log successful send
                EmailLog.objects.create(
                    user=user,
                    email_type=email_type,
                    subject=subject,
                    recipient=user.email,
                    status='SENT',
                    sent_at=timezone.now(),
                    email_content=html_content,
                    campaign_id=campaign_id,
                )

                logger.info(f"Sent {email_type} email to {user.username}")
                return True
            else:
                # Log failed send
                EmailLog.objects.create(
                    user=user,
                    email_type=email_type,
                    subject=subject,
                    recipient=user.email,
                    status='FAILED',
                    error_message='Email send returned 0',
                    campaign_id=campaign_id,
                )

                logger.error(f"Failed to send {email_type} email to {user.username}")
                return False

        except Exception as e:
            # Log error
            EmailLog.objects.create(
                user=user,
                email_type=email_type,
                subject=subject,
                recipient=user.email,
                status='FAILED',
                error_message=str(e),
                campaign_id=campaign_id,
            )

            logger.error(f"Error sending {email_type} email to {user.username}: {e}")
            return False

    def _check_user_preferences(self, user, preference_type):
        """
        Check if user has opted in for specific email type.

        Args:
            user: User instance
            preference_type: Type of preference to check

        Returns:
            bool: True if user wants these emails
        """
        try:
            prefs = EmailPreference.objects.get(user=user)
            return getattr(prefs, preference_type, True)  # Default to True if preference not set
        except EmailPreference.DoesNotExist:
            return True  # Default to sending if no preferences set

    def _get_recommendations(self, user, limit=3):
        """
        Get book recommendations for user.
        This is a simple implementation - in production, this would use
        a more sophisticated recommendation algorithm.

        Args:
            user: User instance
            limit: Maximum number of recommendations

        Returns:
            QuerySet of recommended books
        """
        # Simple recommendation: books not read by user, ordered by popularity
        # In production, this would consider reading history, genres, ratings, etc.
        user_read_books = user.transactions.filter(status__in=['RETURNED', 'ISSUED']).values_list('book_id', flat=True)

        recommendations = Book.objects.exclude(
            id__in=user_read_books
        ).exclude(
            currently_out=True
        ).order_by('-id')[:limit]  # Simple ordering by ID (newest first)

        return recommendations

    def _get_reading_stats(self, user):
        """
        Get reading statistics for user.

        Args:
            user: User instance

        Returns:
            dict: Reading statistics
        """
        # This would typically aggregate from reading logs
        # For now, return mock data
        return {
            'books_this_month': 3,
            'total_books_read': 15,
            'current_streak': 7,
        }


def send_transaction_email(user, template_name, context, email_type, campaign_id):
    """
    Convenience function to send transaction emails.

    Args:
        user: User instance
        template_name: Template path
        context: Template context
        email_type: Email type for logging
        campaign_id: Campaign ID for tracking

    Returns:
        bool: Success status
    """
    service = TransactionEmailService()

    # Determine email type and call appropriate method
    if email_type == 'BOOK_ISSUED':
        return service.send_book_issued_confirmation(context['transaction'], context.get('recommended_books'))
    elif email_type == 'BOOK_RETURNED':
        return service.send_return_confirmation(
            context['transaction'],
            context.get('reading_stats'),
            context.get('achievements')
        )
    elif email_type.startswith('REMINDER_'):
        reminder_type = email_type.replace('REMINDER_', '').lower()
        return service.send_due_reminder(
            context['transaction'],
            reminder_type,
            context.get('days_remaining', 0)
        )
    else:
        # Generic transaction email
        subject = context.get('subject', f'Transaction Update - {context.get("transaction", {}).get("book", {}).get("title", "Book")}')
        return service._send_transaction_email(
            user=user,
            template_name=template_name,
            context=context,
            email_type=email_type,
            campaign_id=campaign_id,
            subject=subject
        )


# Global instance for easy access
transaction_email_service = TransactionEmailService()
