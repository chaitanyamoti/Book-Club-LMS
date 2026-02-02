import qrcode
from io import BytesIO
from django.core.files.base import ContentFile
from django.urls import reverse
from PIL import Image, ImageDraw
import os


def generate_qr_code(book):
    """Generate a QR code that encodes the URL to the book's transaction page."""
    if not book.id:
        return None

    # Generate the URL for the book's scan-and-transact page
    url = reverse('transactions:scan_and_transact', args=[book.id])
    
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    
    qr.add_data(url)
    qr.make(fit=True)

    # Create QR code image
    img = qr.make_image(fill_color="black", back_color="white")

    # Convert to PIL Image for saving
    buffer = BytesIO()
    img.save(buffer, format='PNG')
    buffer.seek(0)

    # Create filename
    filename = f"qr_book_{book.id}.png"

    # Save to Django file field
    book.qr_code.save(filename, ContentFile(buffer.getvalue()), save=False)

    return book.qr_code


def validate_isbn(isbn):
    """Validate ISBN-10 or ISBN-13"""
    if not isbn:
        return True  # Allow empty ISBN

    # Remove hyphens and spaces
    isbn = ''.join(c for c in isbn if c.isdigit() or c == 'X')

    if len(isbn) == 10:
        # ISBN-10 validation
        total = 0
        for i, digit in enumerate(isbn[:-1]):
            if digit == 'X':
                return False
            total += int(digit) * (10 - i)

        check_digit = isbn[-1]
        if check_digit == 'X':
            check_digit = 10
        else:
            check_digit = int(check_digit)

        return (total + check_digit) % 11 == 0

    elif len(isbn) == 13:
        # ISBN-13 validation
        total = 0
        for i, digit in enumerate(isbn[:-1]):
            total += int(digit) * (1 if i % 2 == 0 else 3)

        check_digit = int(isbn[-1])
        return (10 - (total % 10)) % 10 == check_digit

    return False
