from django.contrib import admin
from import_export.admin import ImportExportModelAdmin
from core.models import Book
from .utils import generate_qr_code

# Note: Book is also registered in core.admin to avoid duplicate registrations.
# This module keeps helper code (QR generation) but does not re-register the model.


class BookImportAdmin(ImportExportModelAdmin):
    """Import/Export helper for Book model (not registered if already handled elsewhere)"""
    pass
