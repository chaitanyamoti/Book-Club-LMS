from django.test import TestCase, override_settings
from django.contrib.auth import get_user_model
from django.core import mail
from django.utils import timezone

from core.models import Book, Transaction
from .utils import send_welcome_email, send_overdue_alerts

User = get_user_model()


@override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
class NotificationsTests(TestCase):

    def test_send_welcome_email(self):
        user = User.objects.create_user(username='jdoe', email='jdoe@example.com', password='password')
        send_welcome_email(user)
        self.assertEqual(len(mail.outbox), 1)
        msg = mail.outbox[0]
        self.assertIn('Welcome', msg.subject)
        self.assertIn('Welcome to the Book Club!', msg.body)

    def test_send_overdue_alerts(self):
        user = User.objects.create_user(username='reader', email='reader@example.com', password='password')
        book = Book.objects.create(title='Overdue Book')
        due_date = timezone.now().date() - timezone.timedelta(days=3)
        tx = Transaction.objects.create(user=user, book=book, due_date=due_date)

        sent = send_overdue_alerts()
        self.assertEqual(sent, 1)
        self.assertEqual(len(mail.outbox), 1)
        msg = mail.outbox[0]
        self.assertIn('Overdue Book Alert', msg.subject)
        self.assertIn('You have 1 overdue book(s).', msg.body)
