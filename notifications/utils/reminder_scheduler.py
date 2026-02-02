"""
Smart reminder scheduling system for transaction lifecycle emails.
Handles progressive due date reminders and overdue escalations.
"""
from datetime import timedelta, datetime
from django.utils import timezone
from django.db import models
from transactions.models import Transaction
from notifications.models import EmailLog, EmailPreference
from .email_service import send_transaction_email


class ReminderScheduler:
    """
    Service for scheduling and managing transaction-related email reminders.
    """

    # Reminder types and their scheduling offsets
    REMINDER_SCHEDULE = {
        'gentle_reminder': timedelta(days=-3),  # 3 days before due
        'firm_reminder': timedelta(days=-1),    # 1 day before due
        'final_reminder': timedelta(days=0),    # Due date
        'overdue_warning': timedelta(days=1),   # 1 day after due
        'overdue_escalation': timedelta(days=7), # 7 days after due
    }

    REMINDER_PRIORITIES = {
        'gentle_reminder': 'LOW',
        'firm_reminder': 'MEDIUM',
        'final_reminder': 'HIGH',
        'overdue_warning': 'HIGH',
        'overdue_escalation': 'CRITICAL',
    }

    def schedule_due_reminders(self, transaction):
        """
        Schedule all reminder emails for a transaction based on due date.

        Args:
            transaction: Transaction instance
        """
        reminders_to_schedule = []

        for reminder_type, offset in self.REMINDER_SCHEDULE.items():
            reminder_date = transaction.due_date + offset

            # Only schedule future reminders
            if reminder_date > timezone.now():
                reminders_to_schedule.append({
                    'transaction': transaction,
                    'reminder_type': reminder_type,
                    'scheduled_date': reminder_date,
                    'priority': self.REMINDER_PRIORITIES[reminder_type],
                })

        # Schedule reminders (in a real implementation, this would use Celery)
        for reminder in reminders_to_schedule:
            self._schedule_reminder_email(**reminder)

    def _schedule_reminder_email(self, transaction, reminder_type, scheduled_date, priority):
        """
        Schedule a single reminder email.

        In production, this would create a Celery task or cron job.
        For now, we'll create a placeholder implementation.
        """
        # Check user preferences before scheduling
        try:
            user_prefs = EmailPreference.objects.get(user=transaction.user)
            if not user_prefs.transaction_emails:
                return  # User has opted out of transaction emails
        except EmailPreference.DoesNotExist:
            # Default to sending if no preferences set
            pass

        # Create email log entry for tracking
        email_log = EmailLog.objects.create(
            user=transaction.user,
            email_type=f'REMINDER_{reminder_type.upper()}',
            subject=self._get_reminder_subject(reminder_type, transaction),
            recipient=transaction.user.email,
            status='SCHEDULED',
            campaign_id=f'transaction_{transaction.id}',
        )

        # In production, schedule with Celery:
        # send_reminder_email.apply_async(
        #     args=[email_log.id, transaction.id, reminder_type],
        #     eta=scheduled_date
        # )

        print(f"Scheduled {reminder_type} for {transaction.user.username} at {scheduled_date}")

    def send_immediate_reminder(self, transaction, reminder_type):
        """
        Send an immediate reminder (for testing or manual triggers).

        Args:
            transaction: Transaction instance
            reminder_type: Type of reminder to send
        """
        try:
            user_prefs = EmailPreference.objects.get(user=transaction.user)
            if not user_prefs.transaction_emails:
                print(f"User {transaction.user.username} has opted out of transaction emails")
                return False
        except EmailPreference.DoesNotExist:
            pass

        # Calculate days until due for context
        days_until_due = (transaction.due_date - timezone.now().date()).days

        context = {
            'transaction': transaction,
            'user': transaction.user,
            'days_remaining': max(0, days_until_due),
            'days_until_due': days_until_due,
            'reminder_type': reminder_type,
        }

        template_name = self._get_reminder_template(reminder_type)

        success = send_transaction_email(
            user=transaction.user,
            template_name=template_name,
            context=context,
            email_type=f'REMINDER_{reminder_type.upper()}',
            campaign_id=f'transaction_{transaction.id}',
        )

        if success:
            print(f"Sent {reminder_type} to {transaction.user.username}")
        else:
            print(f"Failed to send {reminder_type} to {transaction.user.username}")

        return success

    def _get_reminder_subject(self, reminder_type, transaction):
        """Get appropriate subject line for reminder type."""
        subjects = {
            'gentle_reminder': f"Friendly reminder: {transaction.book.title} due soon",
            'firm_reminder': f"Important: {transaction.book.title} due tomorrow",
            'final_reminder': f"Final notice: {transaction.book.title} due today",
            'overdue_warning': f"Overdue: {transaction.book.title} needs to be returned",
            'overdue_escalation': f"Urgent: {transaction.book.title} is 7 days overdue",
        }
        return subjects.get(reminder_type, f"Book reminder: {transaction.book.title}")

    def _get_reminder_template(self, reminder_type):
        """Get appropriate template for reminder type."""
        templates = {
            'gentle_reminder': 'email/transactions/gentle_reminder.html',
            'firm_reminder': 'email/transactions/firm_reminder.html',
            'final_reminder': 'email/transactions/final_reminder.html',
            'overdue_warning': 'email/transactions/overdue_warning.html',
            'overdue_escalation': 'email/transactions/overdue_escalation.html',
        }
        return templates.get(reminder_type, 'email/due_reminder.html')

    def get_upcoming_reminders(self, days_ahead=7):
        """
        Get all transactions that need reminders in the next N days.

        Args:
            days_ahead: Number of days to look ahead

        Returns:
            QuerySet of transactions needing reminders
        """
        cutoff_date = timezone.now().date() + timedelta(days=days_ahead)

        # Find transactions that will be due soon
        upcoming_transactions = Transaction.objects.filter(
            due_date__lte=cutoff_date,
            due_date__gte=timezone.now().date(),
            status='ISSUED'
        ).select_related('user', 'book')

        return upcoming_transactions

    def get_overdue_transactions(self, days_overdue=30):
        """
        Get transactions that are overdue and need escalation emails.

        Args:
            days_overdue: Maximum days overdue to consider

        Returns:
            QuerySet of overdue transactions
        """
        cutoff_date = timezone.now().date() - timedelta(days=days_overdue)

        overdue_transactions = Transaction.objects.filter(
            due_date__lt=timezone.now().date(),
            due_date__gte=cutoff_date,
            status='ISSUED'
        ).select_related('user', 'book')

        return overdue_transactions

    def process_daily_reminders(self):
        """
        Process all reminders that should be sent today.
        This would typically be called by a daily cron job.
        """
        today = timezone.now().date()

        # Process upcoming due dates
        upcoming = self.get_upcoming_reminders(days_ahead=3)
        for transaction in upcoming:
            days_until_due = (transaction.due_date - today).days

            # Determine which reminder to send
            if days_until_due == 3:
                self.send_immediate_reminder(transaction, 'gentle_reminder')
            elif days_until_due == 1:
                self.send_immediate_reminder(transaction, 'firm_reminder')
            elif days_until_due == 0:
                self.send_immediate_reminder(transaction, 'final_reminder')

        # Process overdue transactions
        overdue = self.get_overdue_transactions(days_overdue=30)
        for transaction in overdue:
            days_overdue = (today - transaction.due_date).days

            if days_overdue == 1:
                self.send_immediate_reminder(transaction, 'overdue_warning')
            elif days_overdue == 7:
                self.send_immediate_reminder(transaction, 'overdue_escalation')


# Global instance for easy access
reminder_scheduler = ReminderScheduler()
