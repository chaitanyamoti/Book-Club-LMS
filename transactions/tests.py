from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone
from core.models import Book, Transaction
import datetime
import json

class ExtendDueDateTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='password')
        self.book = Book.objects.create(title='Test Book', author='Test Author')
        self.transaction = Transaction.objects.create(
            book=self.book,
            user=self.user,
            transaction_type='ISSUE',
            due_date=timezone.now().date()
        )
        self.client.login(username='testuser', password='password')

    def test_extend_due_date_view(self):
        new_due_date = self.transaction.due_date + datetime.timedelta(days=7)
        response = self.client.post(
            reverse('transactions:extend_due_date', kwargs={'pk': self.transaction.pk}),
            {'new_due_date': new_due_date}
        )
        self.assertEqual(response.status_code, 302)  # Should redirect on success
        self.transaction.refresh_from_db()
        self.assertEqual(self.transaction.due_date, new_due_date)
        self.assertEqual(self.transaction.renewed_count, 1)

class ScanToReturnTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='password')
        self.book = Book.objects.create(title='Test Book', author='Test Author')
        self.transaction = Transaction.objects.create(
            book=self.book,
            user=self.user,
            transaction_type='ISSUE',
            due_date=timezone.now().date()
        )
        self.client.login(username='testuser', password='password')

    def test_scan_to_return_success(self):
        response = self.client.post(
            reverse('transactions:scan_to_return'),
            json.dumps({'book_id': self.book.id}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        self.transaction.refresh_from_db()
        self.assertIsNotNone(self.transaction.return_date)

    def test_scan_to_return_no_open_transaction(self):
        # Mark the transaction as returned
        self.transaction.return_date = timezone.now().date()
        self.transaction.save()

        response = self.client.post(
            reverse('transactions:scan_to_return'),
            json.dumps({'book_id': self.book.id}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertFalse(data['success'])
        self.assertEqual(data['message'], 'No open transaction found for this book.')
