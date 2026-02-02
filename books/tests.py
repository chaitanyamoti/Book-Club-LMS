from django.test import TestCase
import tempfile
import shutil
import os
from django.contrib.auth.models import User
from core.models import Book
from books.utils import validate_isbn, generate_qr_code
from PIL import Image


class UtilsTests(TestCase):
    def test_validate_isbn_valid_and_invalid(self):
        # ISBN-10 valid
        self.assertTrue(validate_isbn('0306406152'))
        # ISBN-10 with X is allowed in last position for check digit
        self.assertTrue(validate_isbn('0306406152'))
        # ISBN-13 valid
        self.assertTrue(validate_isbn('9780306406157'))
        # Empty ISBN allowed
        self.assertTrue(validate_isbn(''))
        # Clearly invalid
        self.assertFalse(validate_isbn('1234567890'))

    def test_generate_qr_code_creates_file(self):
        tmp = tempfile.mkdtemp()
        try:
            with self.settings(MEDIA_ROOT=tmp):
                user = User.objects.create_user(username='qru', password='p')
                book = Book.objects.create(
                    title='QR Test', author='Auth', added_by=user, total_copies=1, available_copies=1
                )
                qr = generate_qr_code(book)
                path = os.path.join(tmp, qr.name)
                self.assertTrue(os.path.exists(path))
                with Image.open(path) as im:
                    self.assertEqual(im.format, 'PNG')
        finally:
            shutil.rmtree(tmp)
