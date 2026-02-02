from django.test import TestCase
from django.contrib.auth.models import User
from core.models import Book
from .forms import BookRequestForm

class BookRequestFormTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='password')
        self.book = Book.objects.create(title='Test Book', author='Test Author')

    def test_book_request_form_valid(self):
        form_data = {
            'request_type': 'WAITLIST',
            'book': self.book.id,
            'reason': 'I want to read this book.'
        }
        form = BookRequestForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_book_request_form_no_book(self):
        form_data = {
            'request_type': 'WAITLIST',
            'reason': 'I want to read this book.'
        }
        form = BookRequestForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('book', form.errors)
