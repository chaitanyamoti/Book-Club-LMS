#!/usr/bin/env python
import os
import django
import sys

# Setup Django
sys.path.append('.')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bookclub.settings')
django.setup()

from core.models import Book

def check_books():
    books = Book.objects.all()
    print(f"Total books: {books.count()}")

    qr_books = books.filter(qr_code__isnull=False)
    print(f"Books with QR codes: {qr_books.count()}")

    print("\nFirst 3 books:")
    for book in books[:3]:
        print(f"{book.title}: QR exists = {bool(book.qr_code)}")

if __name__ == '__main__':
    check_books()
