#!/usr/bin/env python
"""
Test script for email template rendering and validation
"""
import os
import sys
import django
from datetime import datetime, timedelta
from django.conf import settings
from django.template.loader import render_to_string
from django.test import RequestFactory
# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bookclub.settings')
django.setup()

from django.contrib.auth.models import User
from core.models import Book, UserProfile, Transaction
from notifications.models import EmailLog

def create_test_data():
    """Create test data for email template testing"""
    # Create test user
    user, created = User.objects.get_or_create(
        username='testuser',
        defaults={
            'email': 'test@example.com',
            'first_name': 'Test',
            'last_name': 'User'
        }
    )

    # Create user profile
    profile, created = UserProfile.objects.get_or_create(
        user=user,
        defaults={
            'total_books_read': 15,
            'reading_streak_days': 7
        }
    )

    # Create test book
    book, _ = Book.objects.get_or_create(
        title='Test Book Title',
        defaults={
            'author': 'Test Author',
            'isbn': '1234567890',
            'genre': 'Fiction',
            'description': 'A test book for email templates',
            'total_copies': 10,
            'available_copies': 10
        }
    )
    if book.available_copies < 5:
        book.available_copies = 10
        book.total_copies = 10
        book.save()

    # Create test transaction
    transaction = Transaction.objects.filter(user=user, book=book).first()
    if not transaction:
        transaction = Transaction.objects.create(
            user=user,
            book=book,
            issue_date=datetime.now() - timedelta(days=10),
            due_date=datetime.now() + timedelta(days=5),
            transaction_type='ISSUE'
        )

    return user, book, transaction

def test_overdue_alert_template():
    """Test overdue alert email template rendering"""
    print("🧪 Testing overdue alert template...")

    user, book, transaction = create_test_data()

    # Create overdue transaction
    overdue_transaction = Transaction.objects.create(
        user=user,
        book=book,
        issue_date=datetime.now() - timedelta(days=20),
        due_date=datetime.now() - timedelta(days=5),
        transaction_type='ISSUE'
    )
    overdue_transaction.days_overdue = 5  # Simulate overdue days
    overdue_transaction.save()

    context = {
        'user': user,
        'overdue_transactions': [overdue_transaction],
        'club_name': 'Test Book Club'
    }

    try:
        html_content = render_to_string('email/overdue_alert.html', context)
        print("✅ Overdue alert template rendered successfully")

        # Basic validation checks
        checks = [
            ('Base template included', '<!DOCTYPE html>' in html_content),
            ('Header present', '🚨 Overdue Books Alert' in html_content),
            ('User greeting', user.username in html_content),
            ('Book title', book.title in html_content),
            ('Call-to-action buttons', 'Return Books Now' in html_content),
            ('Footer present', 'Book Club' in html_content),
            ('Responsive classes', 'flex' in html_content),
        ]

        for check_name, passed in checks:
            status = "✅" if passed else "❌"
            print(f"  {status} {check_name}")

        return all(passed for _, passed in checks)

    except Exception as e:
        print(f"❌ Overdue alert template failed: {e}")
        return False

def test_book_returned_template():
    """Test book returned email template rendering"""
    print("\n🧪 Testing book returned template...")

    user, book, transaction = create_test_data()

    context = {
        'user': user,
        'book': book,
        'return_date': datetime.now(),
        'condition_notes': 'Book in excellent condition',
        'reading_stats': {
            'books_this_month': 3,
            'total_books_read': 15,
            'current_streak': 7
        },
        'recommended_books': [book],  # Self-recommend for testing
        'achievements': ['Bookworm', 'Speed Reader']
    }

    try:
        html_content = render_to_string('email/book_returned.html', context)
        print("✅ Book returned template rendered successfully")

        # Basic validation checks
        checks = [
            ('Base template included', '<!DOCTYPE html>' in html_content),
            ('Header present', 'Book Returned Successfully' in html_content),
            ('User greeting', user.username in html_content),
            ('Book title', book.title in html_content),
            ('Reading stats', 'Books This Month' in html_content),
            ('Recommendations', 'You Might Also Like' in html_content),
            ('Achievements', 'Achievement Unlocked' in html_content),
            ('Call-to-action buttons', 'Log Reading Progress' in html_content),
        ]

        for check_name, passed in checks:
            status = "✅" if passed else "❌"
            print(f"  {status} {check_name}")

        return all(passed for _, passed in checks)

    except Exception as e:
        print(f"❌ Book returned template failed: {e}")
        return False

def test_responsive_design():
    """Test responsive design elements"""
    print("\n🧪 Testing responsive design...")

    user, book, transaction = create_test_data()

    templates = [
        ('overdue_alert.html', {'user': user, 'overdue_transactions': [transaction], 'club_name': 'Test'}),
        ('book_returned.html', {'user': user, 'book': book, 'return_date': datetime.now()}),
    ]

    responsive_checks = [
        '@media only screen and (max-width: 600px)',
        'flex',
        'justify-content',
        'text-align: center',
        'width: 100%',
    ]

    all_passed = True

    for template_name, context in templates:
        try:
            html_content = render_to_string(f'email/{template_name}', context)

            template_passed = True
            for check in responsive_checks:
                if check not in html_content:
                    print(f"  ❌ {template_name} missing: {check}")
                    template_passed = False
                else:
                    print(f"  ✅ {template_name} has: {check}")

            if template_passed:
                print(f"✅ {template_name} responsive design checks passed")
            else:
                all_passed = False

        except Exception as e:
            print(f"❌ {template_name} responsive test failed: {e}")
            all_passed = False

    return all_passed

def test_tracking_pixel():
    """Test tracking pixel functionality"""
    print("\n🧪 Testing tracking pixel...")

    user, book, transaction = create_test_data()

    # Create test email log
    email_log = EmailLog.objects.create(
        user=user,
        email_type='TEST',
        subject='Test Email',
        recipient=user.email,
        status='SENT'
    )

    context = {
        'user': user,
        'overdue_transactions': [transaction],
        'club_name': 'Test',
        'email_log_uuid': email_log.uuid
    }

    try:
        html_content = render_to_string('email/overdue_alert.html', context)

        # Check for tracking pixel img tag
        if 'tracking pixel' in html_content.lower() and '<img src="' in html_content:
            print("✅ Tracking pixel section present in rendered template")
            return True
        else:
            print("❌ Tracking pixel section missing")
            return False

    except Exception as e:
        print(f"❌ Tracking pixel test failed: {e}")
        return False

def test_email_preferences_integration():
    """Test email preferences URL integration"""
    print("\n🧪 Testing email preferences integration...")

    user, book, transaction = create_test_data()

    context = {
        'user': user,
        'overdue_transactions': [transaction],
        'club_name': 'Test'
    }

    try:
        html_content = render_to_string('email/overdue_alert.html', context)

        # Check for preference links (rendered)
        preference_checks = [
            'Email Preferences',
            '/users/settings/',
        ]

        all_passed = True
        for check in preference_checks:
            if check in html_content:
                print(f"✅ Found: {check}")
            else:
                print(f"❌ Missing: {check}")
                all_passed = False

        return all_passed

    except Exception as e:
        print(f"❌ Email preferences test failed: {e}")
        return False

def main():
    """Run all email template tests"""
    print("🚀 Starting Email Template Testing Suite\n")

    tests = [
        test_overdue_alert_template,
        test_book_returned_template,
        test_responsive_design,
        test_tracking_pixel,
        test_email_preferences_integration,
    ]

    results = []
    for test_func in tests:
        try:
            result = test_func()
            results.append(result)
        except Exception as e:
            print(f"❌ Test {test_func.__name__} crashed: {e}")
            results.append(False)

    print(f"\n📊 Test Results: {sum(results)}/{len(results)} passed")

    if all(results):
        print("🎉 All email template tests passed!")
        return 0
    else:
        print("⚠️ Some tests failed. Please review the output above.")
        return 1

if __name__ == '__main__':
    sys.exit(main())
