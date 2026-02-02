from django.contrib import admin
from import_export import resources
from import_export.admin import ImportExportModelAdmin
from import_export.widgets import ForeignKeyWidget
from django.contrib.auth.models import User
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from django import forms

from .models import Book, Transaction, UserProfile, ReadingLog, BookRequest, ClubSettings
from transactions.forms import TransactionForm


# Import/export resources
class BookResource(resources.ModelResource):
    class Meta:
        model = Book
        fields = ('id', 'title', 'author', 'isbn', 'genre', 'description', 'status', 'total_copies', 'available_copies')


class UserProfileResource(resources.ModelResource):
    user = resources.Field(column_name='username', attribute='user', widget=ForeignKeyWidget(User, 'username'))

    class Meta:
        model = UserProfile
        fields = ('id', 'username', 'phone', 'role', 'is_active')


class TransactionResource(resources.ModelResource):
    user = resources.Field(attribute='user', widget=ForeignKeyWidget(User, 'username'))
    book = resources.Field(attribute='book', widget=ForeignKeyWidget(Book, 'id'))

    class Meta:
        model = Transaction
        fields = ('id', 'book', 'user', 'transaction_type', 'issue_date', 'due_date', 'return_date')


class ReadingLogResource(resources.ModelResource):
    user = resources.Field(attribute='user', widget=ForeignKeyWidget(User, 'username'))
    book = resources.Field(attribute='book', widget=ForeignKeyWidget(Book, 'id'))

    class Meta:
        model = ReadingLog
        fields = ('id', 'user', 'book', 'log_date', 'pages_read', 'minutes_read', 'progress')


class BookRequestResource(resources.ModelResource):
    user = resources.Field(attribute='user', widget=ForeignKeyWidget(User, 'username'))

    class Meta:
        model = BookRequest
        fields = ('id', 'user', 'request_type', 'title', 'author', 'reason', 'status', 'priority', 'created_date')


@admin.register(UserProfile)
class UserProfileAdmin(ImportExportModelAdmin):
    resource_class = UserProfileResource
    list_display = ('user', 'role', 'phone', 'is_active')
    list_filter = ('role', 'is_active')
    search_fields = ('user__username', 'user__email')


@admin.register(Book)
class BookAdmin(ImportExportModelAdmin):
    resource_class = BookResource
    list_display = ('title', 'author', 'isbn', 'status', 'available_copies', 'qr_code_display', 'added_date')
    list_filter = ('status', 'genre')
    search_fields = ('title', 'author', 'isbn')
    actions = ('mark_as_lost', 'mark_as_damaged', 'generate_qr_codes', 'bulk_mark_available', 'bulk_update_status')
    readonly_fields = ('qr_code_display',)

    def qr_code_display(self, obj):
        """Display QR code as image in admin list view."""
        if obj.qr_code:
            return mark_safe(f'<img src="{obj.qr_code.url}" alt="QR code" style="max-width: 50px; max-height: 50px;">')
        return 'No QR'
    qr_code_display.short_description = 'QR Code'

    def save_model(self, request, obj, form, change):
        # Set added_by if missing
        if not obj.added_by:
            obj.added_by = request.user
        super().save_model(request, obj, form, change)

    def mark_as_lost(self, request, queryset):
        """Mark selected books as lost."""
        updated = 0
        for book in queryset:
            book.status = 'LOST'
            book.available_copies = 0
            book.save()
            updated += 1
        messages.success(request, f'{updated} book(s) marked as lost.')
    mark_as_lost.short_description = 'Mark selected books as Lost'

    def mark_as_damaged(self, request, queryset):
        """Mark selected books as damaged."""
        updated = 0
        for book in queryset:
            book.status = 'DAMAGED'
            # decrement available copies but not below zero
            book.available_copies = max(book.available_copies - 1, 0)
            book.save()
            updated += 1
        messages.success(request, f'{updated} book(s) marked as damaged.')
    mark_as_damaged.short_description = 'Mark selected books as Damaged'

    def generate_qr_codes(self, request, queryset):
        """Generate QR codes for selected books."""
        try:
            from books.utils import generate_qr_code
        except ImportError as e:
            messages.error(request, f'QR generation utility not available: {e}')
            return

        generated = 0
        failed = []
        for book in queryset:
            try:
                if not book.qr_code:
                    generate_qr_code(book)
                    book.save()
                    generated += 1
            except Exception as e:
                print(f"ERROR: Could not generate QR code for book {book.id}: {e}")
                failed.append(book.title)
        
        if generated > 0:
            messages.success(request, f'QR code generated for {generated} book(s).')
        if failed:
            messages.error(request, f'Failed to generate QR code for: {", ".join(failed)}.')
    generate_qr_codes.short_description = 'Generate QR codes for selected books'

    def bulk_mark_available(self, request, queryset):
        """Bulk mark selected books as available."""
        updated = 0
        for book in queryset:
            if book.status != 'AVAILABLE':
                book.status = 'AVAILABLE'
                # Reset available copies to total copies if they were reduced
                if book.available_copies < book.total_copies:
                    book.available_copies = book.total_copies
                book.save()
                updated += 1
        messages.success(request, f'{updated} book(s) marked as available.')
    bulk_mark_available.short_description = 'Mark selected books as Available'

    def bulk_update_status(self, request, queryset):
        """Bulk update status for selected books."""
        # This would typically open a form, but for simplicity we'll use a simple approach
        # In a real implementation, you'd create a form to select the new status
        updated = 0
        for book in queryset:
            # Example: Mark as 'MAINTENANCE' if currently available
            if book.status == 'AVAILABLE':
                book.status = 'MAINTENANCE'
                book.save()
                updated += 1
        messages.success(request, f'{updated} book(s) updated to maintenance status.')
    bulk_update_status.short_description = 'Update status to Maintenance'

from django.utils import timezone
from django.contrib import messages

@admin.register(Transaction)
class TransactionAdmin(ImportExportModelAdmin):
    resource_class = TransactionResource
    form = TransactionForm
    list_display = ('id', 'book', 'user', 'transaction_type', 'issue_date', 'due_date', 'return_date', 'is_overdue', 'days_overdue')
    list_filter = ('transaction_type',)
    search_fields = ('book__title', 'user__username')
    actions = ('send_overdue_reminders',)

    # Fix Select2 dropdown display issues
    class Media:
        js = ('admin/js/vendor/jquery/jquery.js', 'admin/js/jquery.init.js')
        css = {
            'all': ('admin/css/forms.css',)
        }

    def is_overdue(self, obj):
        return obj.return_date is None and obj.due_date and obj.due_date < timezone.now().date()
    is_overdue.boolean = True
    is_overdue.short_description = 'Overdue'

    def days_overdue(self, obj):
        if obj.return_date or not obj.due_date:
            return '-'
        delta = (timezone.now().date() - obj.due_date).days
        return delta if delta > 0 else 0
    days_overdue.short_description = 'Days overdue'

    def send_overdue_reminders(self, request, queryset):
        """Admin action to send overdue reminder emails for selected (overdue) transactions."""
        overdue_qs = queryset.filter(return_date__isnull=True, due_date__lt=timezone.now().date())
        if not overdue_qs.exists():
            messages.info(request, 'No overdue transactions selected.')
            return
        try:
            from notifications.utils import send_overdue_alerts_for_qs
            sent = send_overdue_alerts_for_qs(overdue_qs)
            messages.success(request, f'Overdue reminders sent to {sent} users.')
        except Exception as e:
            messages.error(request, f'Error sending reminders: {e}')
    send_overdue_reminders.short_description = 'Send overdue reminder emails for selected transactions'


@admin.register(ReadingLog)
class ReadingLogAdmin(ImportExportModelAdmin):
    resource_class = ReadingLogResource
    list_display = ('user', 'book', 'log_date', 'progress')
    list_filter = ('log_date',)
    search_fields = ('user__username', 'book__title')


@admin.register(BookRequest)
class BookRequestAdmin(ImportExportModelAdmin):
    resource_class = BookRequestResource
    list_display = ('user', 'request_type', 'title', 'status', 'created_date')
    list_filter = ('request_type', 'status')
    search_fields = ('title', 'user__username')


@admin.register(ClubSettings)
class ClubSettingsAdmin(admin.ModelAdmin):
    list_display = ('setting_key', 'setting_value', 'updated_at')
    search_fields = ('setting_key',)
