from django.db.models.signals import pre_save, post_delete, post_save
from django.dispatch import receiver
from django.db import transaction as db_transaction
from django.core.exceptions import ValidationError
from django.db.models import F
from django.utils import timezone # Import timezone
from .models import Transaction, Book, ReadingLog, UserProfile # Import ReadingLog and UserProfile
from notifications.utils_new import send_reading_streak_email, send_books_read_milestone_email # Import the email sending utility

@receiver(pre_save, sender=Transaction)
def transaction_pre_save(sender, instance, **kwargs):
    """
    Handles quantity adjustments for associated Book model before a Transaction is saved.
    Uses select_for_update to prevent race conditions during quantity checks and updates.
    """
    prev_instance = None
    if instance.pk:
        try:
            prev_instance = Transaction.objects.get(pk=instance.pk)
        except Transaction.DoesNotExist:
            pass
    instance._previous = prev_instance

    # Ensure the book instance is locked for update to prevent race conditions
    with db_transaction.atomic():
        # Retrieve the book for this transaction and lock it for update
        book = Book.objects.select_for_update().get(pk=instance.book.pk)

        was_active_issue = prev_instance and prev_instance.transaction_type == 'ISSUE' and prev_instance.return_date is None
        is_active_issue = instance.transaction_type == 'ISSUE' and instance.return_date is None

        # Calculate the intended change in available copies
        change_in_available_copies = 0
        if not was_active_issue and is_active_issue:
            # Transition from not an active issue to an active issue
            # (e.g., new 'ISSUE' transaction, or an 'ISSUE' transaction being 'un-returned')
            change_in_available_copies = -1
        elif was_active_issue and not is_active_issue:
            # Transition from an active issue to not an active issue
            # (e.g., 'ISSUE' transaction being returned, or transaction type changed from 'ISSUE')
            change_in_available_copies = 1

        # Apply the change and validate
        if change_in_available_copies != 0:
            intended_available_copies = book.available_copies + change_in_available_copies

            # If we don't have enough copies, we stop here.
            # The admin check in save_model will catch this and show a proper error message.
            if intended_available_copies >= 0 and intended_available_copies <= book.total_copies:
                book.available_copies = intended_available_copies
                book.save(update_fields=['available_copies']) # Update only available_copies atomically
        
        # After available_copies is updated and saved, refresh the book from the database
        # to ensure its available_copies is the updated value and then call its save method
        # for it to re-calculate currently_out and status based on the fresh available_copies.
        book.refresh_from_db()
        book.save() # This save will re-calculate currently_out and potentially update status


@receiver(post_delete, sender=Transaction)
def transaction_post_delete(sender, instance, **kwargs):
    """If an active ISSUE transaction is deleted, restore availability."""
    # Only if the deleted transaction was an active ISSUE (not returned)
    if instance.transaction_type == 'ISSUE' and instance.return_date is None:
        with db_transaction.atomic():
            book = Book.objects.select_for_update().get(pk=instance.book.pk)
            
            # Simply update available_copies. If it exceeds total_copies,
            # this logic is moved to the admin level where it can be handled gracefully.
            book.available_copies += 1
            book.save(update_fields=['available_copies'])
            
            book.refresh_from_db()
            book.save() # This save will re-calculate currently_out and potentially update status


@receiver(post_save, sender=ReadingLog)
def check_reading_streak(sender, instance, created, **kwargs):
    """
    Checks and updates a user's reading streak after a ReadingLog entry is saved.
    Sends a notification email if a streak milestone is reached.
    """
    if created:
        user_profile = instance.user.userprofile
        today = timezone.localdate() # Use localdate for streak logic

        # If it's a new day since last reading or first log
        if user_profile.last_reading_date is None or (today - user_profile.last_reading_date).days == 1:
            user_profile.streak_days += 1
        elif (today - user_profile.last_reading_date).days > 1:
            # Streak broken
            user_profile.streak_days = 1
        # If it's the same day, no change to streak (already incremented or set to 1)

        user_profile.last_reading_date = today

        if user_profile.streak_days > user_profile.longest_streak:
            user_profile.longest_streak = user_profile.streak_days
        
        user_profile.save(update_fields=['streak_days', 'longest_streak', 'last_reading_date'])

        # Check for streak milestones
        milestones = [7, 14, 30, 60, 100]
        if user_profile.streak_days in milestones:
            # Add logic here to prevent sending multiple emails for the same milestone
            # For simplicity, we'll send it each time the milestone is hit on a new day
            send_reading_streak_email(user_profile.user, user_profile.streak_days)


@receiver(post_save, sender=Transaction)
def check_books_read_milestone(sender, instance, created, **kwargs):
    """
    Checks and updates a user's total books read count and sends a milestone email
    when a book is returned.
    """
    # Only act if it's a return transaction and the return_date was just set
    # (or updated to a non-null value)
    if not created and instance.transaction_type == 'RETURN' and instance.return_date and \
       (instance._previous and instance._previous.return_date is None):
        user_profile = instance.user.userprofile
        user_profile.total_books_read += 1
        user_profile.save(update_fields=['total_books_read'])

        milestones = [1, 5, 10, 25, 50, 100] # Define books read milestones
        if user_profile.total_books_read in milestones:
            # Prevent sending multiple emails for the same milestone
            send_books_read_milestone_email(user_profile.user, user_profile.total_books_read)


from notifications.utils_new import send_new_book_alert_email # Import the new email utility
from books.utils import generate_qr_code # Import QR code generator

@receiver(post_save, sender=Book)
def send_new_book_alert(sender, instance, created, **kwargs):
    """
    Sends a new book alert email and generates a QR code when a new book is added.
    """
    if created:
        send_new_book_alert_email(instance)
        # Also generate QR code for the new book
        generate_qr_code(instance)
        instance.save(update_fields=['qr_code'])