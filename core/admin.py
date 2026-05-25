import logging
from django.contrib import admin, messages
from django.contrib.admin.sites import NotRegistered
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from django.template.response import TemplateResponse
from import_export import resources
from import_export.admin import ImportExportModelAdmin
from import_export.widgets import ForeignKeyWidget
from django.contrib.auth.models import Group, User
from django.urls import reverse
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from django import forms
from django.http import HttpResponseRedirect
from django.core.exceptions import ValidationError

from .models import Book, Transaction, UserProfile, ReadingLog, BookRequest, ClubSettings
from transactions.forms import TransactionForm

logger = logging.getLogger(__name__)

class FriendlyImportExportMixin:
    """Mixin to provide user-friendly error messages during import/export."""
    def import_action(self, request, *args, **kwargs):
        try:
            return super().import_action(request, *args, **kwargs)
        except Exception as e:
            error_msg = str(e)
            # Provide more context for common errors
            if "tablib" in error_msg.lower() or "format" in error_msg.lower():
                user_msg = "The file format is not supported or the file is corrupted. Please use CSV, XLS, or XLSX."
            else:
                user_msg = f"Error processing import file: {error_msg}. Please check your data and try again."
            
            messages.error(request, user_msg)
            logger.exception("Import Error")
            # Redirect back to the changelist
            return HttpResponseRedirect(request.path_info.split('/import/')[0] + '/')

    def export_action(self, request, *args, **kwargs):
        try:
            return super().export_action(request, *args, **kwargs)
        except Exception as e:
            messages.error(request, f"Error during export: {str(e)}")
            logger.exception("Export Error")
            return HttpResponseRedirect(request.path_info.split('/export/')[0] + '/')



# Hide Django's default Groups section from the admin side panel.
try:
    admin.site.unregister(Group)
except NotRegistered:
    pass


try:
    admin.site.unregister(User)
except NotRegistered:
    pass


# Import/export resources
class BookResource(resources.ModelResource):
    class Meta:
        model = Book
        fields = ('id', 'title', 'author', 'isbn', 'genre', 'description', 'status', 'total_copies', 'available_copies')
        skip_errors = True

    def before_save_instance(self, instance, using_transactions, dry_run):
        """Clean data before saving to avoid IntegrityErrors."""
        if not instance.title:
            instance.title = "Untitled Book"
        if not instance.author:
            instance.author = "Unknown Author"
        if instance.genre is None:
            instance.genre = ""
        if instance.description is None:
            instance.description = ""
        if not instance.isbn:
            import uuid
            instance.isbn = str(uuid.uuid4())[:13]
        
        # Ensure availability copies are valid
        if instance.total_copies is None:
            instance.total_copies = 1
        if instance.available_copies is None:
            instance.available_copies = instance.total_copies
            
        super().before_save_instance(instance, using_transactions, dry_run)


class UserProfileResource(resources.ModelResource):
    user = resources.Field(column_name='username', attribute='user', widget=ForeignKeyWidget(User, 'username'))

    class Meta:
        model = UserProfile
        fields = ('id', 'username', 'phone', 'role', 'is_active')
        skip_errors = True

    def before_save_instance(self, instance, using_transactions, dry_run):
        if instance.phone is None:
            instance.phone = ""
        if not instance.role:
            instance.role = "MEMBER"
        super().before_save_instance(instance, using_transactions, dry_run)


class TransactionResource(resources.ModelResource):
    user = resources.Field(attribute='user', widget=ForeignKeyWidget(User, 'username'))
    book = resources.Field(attribute='book', widget=ForeignKeyWidget(Book, 'id'))

    class Meta:
        model = Transaction
        fields = ('id', 'book', 'user', 'transaction_type', 'issue_date', 'due_date', 'return_date')
        skip_errors = True

    def before_save_instance(self, instance, using_transactions, dry_run):
        if instance.admin_notes is None:
            instance.admin_notes = ""
        if instance.condition_notes is None:
            instance.condition_notes = ""
        if not instance.due_date:
            from django.utils import timezone
            from datetime import timedelta
            instance.due_date = timezone.now().date() + timedelta(days=14)
        super().before_save_instance(instance, using_transactions, dry_run)


class ReadingLogResource(resources.ModelResource):
    user = resources.Field(attribute='user', widget=ForeignKeyWidget(User, 'username'))
    book = resources.Field(attribute='book', widget=ForeignKeyWidget(Book, 'id'))

    class Meta:
        model = ReadingLog
        fields = ('id', 'user', 'book', 'log_date', 'pages_read', 'minutes_read', 'progress')
        skip_errors = True


class BookRequestResource(resources.ModelResource):
    user = resources.Field(attribute='user', widget=ForeignKeyWidget(User, 'username'))

    class Meta:
        model = BookRequest
        fields = ('id', 'user', 'request_type', 'title', 'author', 'reason', 'status', 'priority', 'created_date')
        skip_errors = True


class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    extra = 0
    fields = (
        'phone',
        'avatar',
        'role',
        'reading_preferences',
        'is_active',
        'email_overdue_reminders',
        'email_due_date_alerts',
        'email_book_returned',
        'email_new_announcements',
        'email_weekly_digest',
        'total_books_read',
    )


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'profile_link')
    list_filter = ('is_staff', 'groups')
    # list_filter = ('is_staff', 'is_superuser', 'is_active', 'groups')
    inlines = (UserProfileInline,)

    def profile_link(self, obj):
        try:
            profile = obj.userprofile
        except UserProfile.DoesNotExist:
            return '-'

        url = reverse('admin:core_userprofile_change', args=[profile.pk])
        return format_html('<a href="{}">View profile</a>', url)
    profile_link.short_description = 'Profile'


@admin.register(UserProfile)
class UserProfileAdmin(FriendlyImportExportMixin, ImportExportModelAdmin):
    resource_class = UserProfileResource
    list_display = ('user', 'role', 'phone', 'is_active')
    list_filter = ('role', 'is_active')
    search_fields = ('user__username', 'user__email')


@admin.register(Book)
class BookAdmin(FriendlyImportExportMixin, ImportExportModelAdmin):
    resource_class = BookResource
    list_display = ('title', 'author', 'isbn', 'status', 'available_copies', 'qr_code_display', 'added_date')
    list_filter = ('status', 'genre')
    search_fields = ('title', 'author', 'isbn')
    actions = ('mark_as_lost', 'mark_as_damaged', 'generate_qr_codes', 'print_qr_sheet', 'bulk_mark_available', 'bulk_update_status')
    readonly_fields = ('qr_code_display',)

    def qr_code_display(self, obj):
        """Display QR code as image in admin list view."""
        url = reverse('books:generate_qr', args=[obj.id])
        return mark_safe(f'<img src="{url}" alt="QR code" style="max-width: 50px; max-height: 50px;">')
    qr_code_display.short_description = 'QR Code'

    def save_model(self, request, obj, form, change):
        # Set added_by if missing
        if not obj.added_by:
            obj.added_by = request.user
        try:
            super().save_model(request, obj, form, change)
        except Exception as e:
            messages.error(request, f"Error saving book: {str(e)}")

    def mark_as_lost(self, request, queryset):
        """Mark selected books as lost."""
        try:
            updated = 0
            for book in queryset:
                book.status = 'LOST'
                book.available_copies = 0
                book.save()
                updated += 1
            messages.success(request, f'{updated} book(s) marked as lost.')
        except Exception as e:
            messages.error(request, f"Error marking books as lost: {str(e)}")
    mark_as_lost.short_description = 'Mark selected books as Lost'

    def mark_as_damaged(self, request, queryset):
        """Mark selected books as damaged."""
        try:
            updated = 0
            for book in queryset:
                book.status = 'DAMAGED'
                # decrement available copies but not below zero
                book.available_copies = max(book.available_copies - 1, 0)
                book.save()
                updated += 1
            messages.success(request, f'{updated} book(s) marked as damaged.')
        except Exception as e:
            messages.error(request, f"Error marking books as damaged: {str(e)}")
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
                logger.error(f"Could not generate QR code for book {book.id}: {e}")
                failed.append(book.title)
        
        if generated > 0:
            messages.success(request, f'QR code generated for {generated} book(s).')
        if failed:
            messages.error(request, f'Failed to generate QR code for: {", ".join(failed)}.')
    generate_qr_codes.short_description = 'Generate QR codes for selected books'

    def print_qr_sheet(self, request, queryset):
        """Open a printable QR sheet for the selected books."""
        try:
            from books.utils import generate_qr_code
        except ImportError as e:
            messages.error(request, f'QR generation utility not available: {e}')
            return

        books = list(queryset.order_by('title', 'id'))
        generated = 0
        failed = []

        for book in books:
            if book.qr_code:
                continue

            try:
                generate_qr_code(book)
                book.save(update_fields=['qr_code'])
                generated += 1
            except Exception as e:
                logger.error(f"Could not generate QR code for book {book.id}: {e}")
                failed.append(book.title)

        if generated > 0:
            messages.success(request, f'QR code generated for {generated} selected book(s).')
        if failed:
            messages.error(request, f'Failed to generate QR code for: {", ".join(failed)}.')

        context = {
            **self.admin_site.each_context(request),
            'title': 'Print QR Codes',
            'books': books,
        }
        return TemplateResponse(request, 'admin/core/book/print_qr_sheet.html', context)
    print_qr_sheet.short_description = 'Print QR sheet for selected books'

    def bulk_mark_available(self, request, queryset):
        """Bulk mark selected books as available."""
        try:
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
        except Exception as e:
            messages.error(request, f"Error marking books as available: {str(e)}")
    bulk_mark_available.short_description = 'Mark selected books as Available'

    def bulk_update_status(self, request, queryset):
        """Bulk update status for selected books."""
        try:
            updated = 0
            for book in queryset:
                # Example: Mark as 'MAINTENANCE' if currently available
                if book.status == 'AVAILABLE':
                    book.status = 'MAINTENANCE'
                    book.save()
                    updated += 1
            messages.success(request, f'{updated} book(s) updated to maintenance status.')
        except Exception as e:
            messages.error(request, f"Error updating book status: {str(e)}")
    bulk_update_status.short_description = 'Update status to Maintenance'

from django.utils import timezone

@admin.register(Transaction)
class TransactionAdmin(FriendlyImportExportMixin, ImportExportModelAdmin):
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

    def save_model(self, request, obj, form, change):
        # Availability check is now handled in TransactionForm.clean()
        try:
            super().save_model(request, obj, form, change)
        except ValidationError as e:
            messages.error(request, str(e))
        except Exception as e:
            messages.error(request, f"Error saving transaction: {str(e)}")

    def delete_model(self, request, obj):
        try:
            # Check if this is an active issue that would cause an availability error
            if obj.transaction_type == 'ISSUE' and obj.return_date is None:
                if obj.book.available_copies + 1 > obj.book.total_copies:
                    messages.error(request, f"Cannot delete issued transaction for '{obj.book.title}': Available copies would exceed total copies ({obj.book.total_copies}).")
                    return # Don't delete
            
            # Proceed with normal deletion
            super().delete_model(request, obj)
        except Exception as e:
            messages.error(request, f"Error deleting transaction: {str(e)}")

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


# @admin.register(ReadingLog)
# class ReadingLogAdmin(ImportExportModelAdmin):
#     resource_class = ReadingLogResource
#     list_display = ('user', 'book', 'log_date', 'progress')
#     list_filter = ('log_date',)
#     search_fields = ('user__username', 'book__title')


# @admin.register(BookRequest)
# class BookRequestAdmin(ImportExportModelAdmin):
#     resource_class = BookRequestResource
#     list_display = ('user', 'request_type', 'title', 'status', 'created_date')
#     list_filter = ('request_type', 'status')
#     search_fields = ('title', 'user__username')


# @admin.register(ClubSettings)
# class ClubSettingsAdmin(admin.ModelAdmin):
#     list_display = ('setting_key', 'setting_value', 'updated_at')
#     search_fields = ('setting_key',)
