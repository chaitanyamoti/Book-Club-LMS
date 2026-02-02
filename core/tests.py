from django.test import TestCase
from django.utils import timezone
from django.contrib.auth.models import User
from core.models import Book, Transaction
import datetime


class BookModelTests(TestCase):
    def test_auto_generate_isbn_when_missing(self):
        user = User.objects.create_user(username='u', password='p')
        book = Book.objects.create(
            title='Title', author='Author', added_by=user, total_copies=1, available_copies=1
        )
        self.assertIsNotNone(book.isbn)
        self.assertEqual(len(book.isbn), 13)

    def test_currently_out_calculation(self):
        user = User.objects.create_user(username='testuser', password='p')
        book = Book.objects.create(
            title='Test Book', author='Test Author', added_by=user, total_copies=5, available_copies=3
        )
        self.assertEqual(book.currently_out, 2)

        # Test that it updates on save
        book.available_copies = 1
        book.save()
        self.assertEqual(book.currently_out, 4)



class TransactionModelTests(TestCase):
    def test_is_overdue_true_when_due_passed_and_not_returned(self):
        user = User.objects.create_user(username='u2', password='p')
        book = Book.objects.create(title='T2', author='A2', added_by=user, total_copies=1, available_copies=0)
        due = timezone.now().date() - datetime.timedelta(days=5)
        trans = Transaction.objects.create(
            book=book, user=user, transaction_type='ISSUE', due_date=due, created_by=user
        )
        self.assertTrue(trans.is_overdue())

    def test_is_overdue_false_when_returned_or_due_future(self):
        user = User.objects.create_user(username='u3', password='p')
        book = Book.objects.create(title='T3', author='A3', added_by=user, total_copies=1, available_copies=1)
        due = timezone.now().date() + datetime.timedelta(days=5)
        trans = Transaction.objects.create(
            book=book, user=user, transaction_type='ISSUE', due_date=due, created_by=user
        )
        self.assertFalse(trans.is_overdue())
        trans.return_date = timezone.now().date()
        trans.save()
        self.assertFalse(trans.is_overdue())


class DashboardDataTests(TestCase):
    def test_dashboard_data_endpoint_requires_login_and_returns_correct_counts(self):
        # Create an active user (signals should create UserProfile)
        user = User.objects.create_user(username='dashuser', password='password')
        # Create some books and transactions
        book1 = Book.objects.create(title='B1', author='A1', added_by=user)
        book2 = Book.objects.create(title='B2', author='A2', added_by=user)
        trans = Transaction.objects.create(book=book1, user=user, transaction_type='ISSUE', due_date=timezone.now().date())

        # Try unauthenticated
        response = self.client.get('/dashboard/data/')
        self.assertEqual(response.status_code, 302)  # Redirect to login

        # Login and access
        self.client.login(username='dashuser', password='password')
        response = self.client.get('/dashboard/data/')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['total_books'], 2)
        self.assertEqual(data['total_issues'], 1)

    def test_issue_decreases_available_copies(self):
        user = User.objects.create_user(username='issue_user', password='password')
        book = Book.objects.create(title='BI', author='AI', added_by=user, total_copies=2, available_copies=2)
        tx = Transaction.objects.create(book=book, user=user, transaction_type='ISSUE', due_date=timezone.now().date(), created_by=user)
        book.refresh_from_db()
        self.assertEqual(book.available_copies, 1)

    def test_return_increases_available_copies(self):
        user = User.objects.create_user(username='return_user', password='password')
        book = Book.objects.create(title='BR', author='AR', added_by=user, total_copies=1, available_copies=1)
        tx = Transaction.objects.create(book=book, user=user, transaction_type='ISSUE', due_date=timezone.now().date(), created_by=user)
        # now return
        tx.return_date = timezone.now().date()
        tx.transaction_type = 'RETURN'
        tx.save()
        book.refresh_from_db()
        self.assertEqual(book.available_copies, 1)
