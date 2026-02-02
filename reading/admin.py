from django.contrib import admin
from core.models import ReadingLog

# ReadingLog is registered in core.admin to avoid duplicate registrations.
# This file can be extended for app-specific admin customizations if needed.


class ReadingLogAdmin(admin.ModelAdmin):
    list_display = ('user', 'book', 'log_date', 'progress')
    list_filter = ('log_date',)
    search_fields = ('user__username', 'book__title')
