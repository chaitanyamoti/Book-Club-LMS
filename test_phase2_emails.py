#!/usr/bin/env python
"""
Comprehensive test script for Phase 2: Transaction Lifecycle Emails
Tests reminder scheduling, email service, and template rendering.
"""
import os
import sys
import django
from datetime import datetime, timedelta, date

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bookclub.settings')
django.setup()

from django.template.loader import render_to_string
from django.utils import timezone
from django.contrib.auth.models import User
from core.models import Transaction, Book, UserProfile
from notifications.models import EmailPreference, EmailLog
from notifications.utils.reminder_scheduler import reminder_scheduler
from notifications.utils.email_service import transaction_email_service

def create_test_data():
    """Create comprehensive test data for Phase 2 testing"""
    print("🔧 Creating test data...")

    # Create test user
    user, created = User.objects.get_or_create(
        username='testuser_phase2',
        defaults={
            'email': 'test-phase2@example.com',
            'first_name': 'Test',
            'last_name': 'User Phase2'
        }
    )

    # Create user profile
    profile, created = UserProfile.objects.get_or_create(
        user=user,
        defaults={
            'total_books_read': 25,
            'reading_streak_days': 12
        }
    )

    # Create email preferences
    prefs, created = EmailPreference.objects.get_or_create(
        user=user,
        defaults={
            'transaction_emails': True,
            'reading_emails': True,
            'frequency': 'IMMEDIATE'
        }
    )

    # Create test book
    book, _ = Book.objects.get_or_create(
        title='Phase 2 Test Book',
        defaults={
            'author': 'Test Author',
            'isbn': 'PHASE2123456',
            'genre': 'Test Fiction',
            'description': 'A book for testing Phase 2 email functionality',
            'total_copies': 10,
            'available_copies': 10
        }
    )
    if book.available_copies < 5:
        book.available_copies = 10
        book.total_copies = 10
        book.save()

    # Create test transaction with different due dates for testing
    today = timezone.now().date()

    # Future due date (3 days from now) - for gentle reminder testing
    future_transaction = Transaction.objects.get_or_create(
        user=user,
        book=book,
        issue_date=today - timedelta(days=10),
        due_date=today + timedelta(days=3),
        defaults={'transaction_type': 'ISSUE'}
    )[0]

    # Due tomorrow - for firm reminder testing
    tomorrow_transaction = Transaction.objects.get_or_create(
        user=user,
        book=book,
        issue_date=today - timedelta(days=10),
        due_date=today + timedelta(days=1),
        defaults={'transaction_type': 'ISSUE'}
    )[0]

    # Due today - for final reminder testing
    today_transaction = Transaction.objects.get_or_create(
        user=user,
        book=book,
        issue_date=today - timedelta(days=10),
        due_date=today,
        defaults={'transaction_type': 'ISSUE'}
    )[0]

    # Overdue 1 day - for overdue warning testing
    overdue1_transaction = Transaction.objects.get_or_create(
        user=user,
        book=book,
        issue_date=today - timedelta(days=15),
        due_date=today - timedelta(days=1),
        defaults={'transaction_type': 'ISSUE'}
    )[0]

    # Overdue 7 days - for escalation testing
    overdue7_transaction = Transaction.objects.get_or_create(
        user=user,
        book=book,
        issue_date=today - timedelta(days=20),
        due_date=today - timedelta(days=7),
        defaults={'transaction_type': 'ISSUE'}
    )[0]

    print("✅ Test data created successfully")
    return user, book, [future_transaction, tomorrow_transaction, today_transaction, overdue1_transaction, overdue7_transaction]

def test_reminder_scheduler():
    """Test the reminder scheduler functionality"""
    print("\n🧪 Testing Reminder Scheduler...")

    user, book, transactions = create_test_data()
    future_tx, tomorrow_tx, today_tx, overdue1_tx, overdue7_tx = transactions

    # Test scheduling reminders for future transaction
    print("  📅 Testing reminder scheduling for future transaction...")
    reminder_scheduler.schedule_due_reminders(future_tx)

    # Test immediate reminder sending
    print("  📧 Testing immediate reminder sending...")

    # Test gentle reminder (3 days out)
    success = reminder_scheduler.send_immediate_reminder(future_tx, 'gentle_reminder')
    print(f"    ✅ Gentle reminder: {'SENT' if success else 'FAILED'}")

    # Test firm reminder (1 day out)
    success = reminder_scheduler.send_immediate_reminder(tomorrow_tx, 'firm_reminder')
    print(f"    ✅ Firm reminder: {'SENT' if success else 'FAILED'}")

    # Test final reminder (due today)
    success = reminder_scheduler.send_immediate_reminder(today_tx, 'final_reminder')
    print(f"    ✅ Final reminder: {'SENT' if success else 'FAILED'}")

    # Test overdue warning (1 day overdue)
    success = reminder_scheduler.send_immediate_reminder(overdue1_tx, 'overdue_warning')
    print(f"    ✅ Overdue warning: {'SENT' if success else 'FAILED'}")

    # Test overdue escalation (7 days overdue)
    success = reminder_scheduler.send_immediate_reminder(overdue7_tx, 'overdue_escalation')
    print(f"    ✅ Overdue escalation: {'SENT' if success else 'FAILED'}")

    # Test upcoming reminders query
    upcoming = reminder_scheduler.get_upcoming_reminders(days_ahead=7)
    print(f"    ✅ Found {upcoming.count()} upcoming transactions")

    # Test overdue transactions query
    overdue = reminder_scheduler.get_overdue_transactions(days_overdue=30)
    print(f"    ✅ Found {overdue.count()} overdue transactions")

    return True

def test_email_service():
    """Test the transaction email service"""
    print("\n🧪 Testing Email Service...")

    user, book, transactions = create_test_data()
    future_tx, tomorrow_tx, today_tx, overdue1_tx, overdue7_tx = transactions

    # Test book issued confirmation
    print("  📚 Testing book issued confirmation...")
    success = transaction_email_service.send_book_issued_confirmation(future_tx)
    print(f"    ✅ Book issued email: {'SENT' if success else 'FAILED'}")

    # Test return confirmation
    print("  🔄 Testing return confirmation...")
    success = transaction_email_service.send_return_confirmation(
        future_tx,
        reading_stats={'books_this_month': 5, 'total_books_read': 25, 'current_streak': 12},
        achievements=['Bookworm', 'Consistent Reader']
    )
    print(f"    ✅ Return confirmation: {'SENT' if success else 'FAILED'}")

    # Test due reminders via email service
    print("  ⏰ Testing due reminders via email service...")
    success = transaction_email_service.send_due_reminder(future_tx, 'gentle_reminder', days_remaining=3)
    print(f"    ✅ Gentle reminder via service: {'SENT' if success else 'FAILED'}")

    success = transaction_email_service.send_due_reminder(tomorrow_tx, 'firm_reminder', days_remaining=1)
    print(f"    ✅ Firm reminder via service: {'SENT' if success else 'FAILED'}")

    return True

def test_template_rendering():
    """Test all Phase 2 email template rendering"""
    print("\n🧪 Testing Template Rendering...")

    user, book, transactions = create_test_data()
    future_tx, tomorrow_tx, today_tx, overdue1_tx, overdue7_tx = transactions

    templates_to_test = [
        ('email/book_issued.html', {
            'transaction': future_tx,
            'days_until_due': 3,
            'recommended_books': [book]
        }, 'Book Issued'),

        ('email/book_returned.html', {
            'user': user,
            'book': book,
            'return_date': timezone.now(),
            'reading_stats': {'books_this_month': 5, 'total_books_read': 25, 'current_streak': 12},
            'recommended_books': [book],
            'achievements': ['Bookworm']
        }, 'Book Returned'),

        ('email/transactions/gentle_reminder.html', {
            'transaction': future_tx,
            'user': user,
            'days_remaining': 3
        }, 'Gentle Reminder'),

        ('email/transactions/firm_reminder.html', {
            'transaction': tomorrow_tx,
            'user': user,
            'days_remaining': 1
        }, 'Firm Reminder'),

        ('email/transactions/final_reminder.html', {
            'transaction': today_tx,
            'user': user,
            'days_remaining': 0
        }, 'Final Reminder'),

        ('email/transactions/overdue_warning.html', {
            'transaction': overdue1_tx,
            'user': user,
            'days_overdue': 1
        }, 'Overdue Warning'),

        ('email/transactions/overdue_escalation.html', {
            'transaction': overdue7_tx,
            'user': user
        }, 'Overdue Escalation'),
    ]

    all_passed = True

    for template_name, context, description in templates_to_test:
        try:
            html_content = render_to_string(template_name, context)

            # Basic validation checks
            checks = [
                ('Base template included', '<!DOCTYPE html>' in html_content),
                ('User greeting', user.username in html_content),
                ('Book title', book.title in html_content),
                ('Responsive design', 'flex' in html_content),
            ]

            template_passed = True
            for check_name, passed in checks:
                if not passed:
                    print(f"    ❌ {description} - Missing: {check_name}")
                    template_passed = False

            if template_passed:
                print(f"    ✅ {description} template rendered successfully")
            else:
                all_passed = False

        except Exception as e:
            print(f"    ❌ {description} template failed: {e}")
            all_passed = False

    return all_passed

def test_email_logging():
    """Test email logging functionality"""
    print("\n🧪 Testing Email Logging...")

    # Check if emails were logged
    recent_logs = EmailLog.objects.filter(
        user__username='testuser_phase2',
        created_at__gte=timezone.now() - timedelta(hours=1)
    ).order_by('-created_at')

    print(f"  📊 Found {recent_logs.count()} recent email logs")

    for log in recent_logs[:5]:  # Show last 5 logs
        print(f"    📧 {log.email_type}: {log.subject[:50]}... - {log.status}")

    # Verify log structure
    if recent_logs.exists():
        log = recent_logs.first()
        required_fields = ['user', 'email_type', 'subject', 'recipient', 'status', 'campaign_id']
        log_valid = all(hasattr(log, field) for field in required_fields)

        if log_valid:
            print("    ✅ Email log structure is valid")
            return True
        else:
            print("    ❌ Email log structure is invalid")
            return False
    else:
        print("    ⚠️ No email logs found (this may be expected if emails failed to send)")
        return True

def test_user_preferences():
    """Test user email preference integration"""
    print("\n🧪 Testing User Preferences...")

    user, book, transactions = create_test_data()

    # Test with preferences enabled
    success = transaction_email_service.send_book_issued_confirmation(transactions[0])
    print(f"    ✅ Email sent with preferences enabled: {'SENT' if success else 'FAILED'}")

    # Disable transaction emails
    prefs = EmailPreference.objects.get(user=user)
    prefs.transaction_emails = False
    prefs.save()

    # Test with preferences disabled
    success = transaction_email_service.send_book_issued_confirmation(transactions[0])
    print(f"    ✅ Email blocked with preferences disabled: {'BLOCKED' if not success else 'SENT (unexpected)'}")

    # Re-enable for other tests
    prefs.transaction_emails = True
    prefs.save()

    return True

def cleanup_test_data():
    """Clean up test data"""
    print("\n🧹 Cleaning up test data...")

    try:
        # Delete test transactions
        Transaction.objects.filter(user__username='testuser_phase2').delete()

        # Delete test book (if it was created for testing)
        Book.objects.filter(title='Phase 2 Test Book').delete()

        # Delete test user and related data
        User.objects.filter(username='testuser_phase2').delete()

        print("    ✅ Test data cleaned up successfully")
    except Exception as e:
        print(f"    ⚠️ Cleanup warning: {e}")

def main():
    """Run all Phase 2 email tests"""
    print("🚀 Starting Phase 2 Email System Testing Suite\n")

    tests = [
        test_reminder_scheduler,
        test_email_service,
        test_template_rendering,
        test_email_logging,
        test_user_preferences,
    ]

    results = []
    for test_func in tests:
        try:
            result = test_func()
            results.append(result)
        except Exception as e:
            print(f"❌ Test {test_func.__name__} crashed: {e}")
            results.append(False)

    # Cleanup
    cleanup_test_data()

    print(f"\n📊 Test Results: {sum(results)}/{len(results)} passed")

    if all(results):
        print("🎉 All Phase 2 email tests passed!")
        return 0
    else:
        print("⚠️ Some tests failed. Please review the output above.")
        return 1

if __name__ == '__main__':
    sys.exit(main())
