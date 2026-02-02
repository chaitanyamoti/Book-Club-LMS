from django.contrib import admin
from core.models import BookRequest

# BookRequest is registered in core.admin to avoid duplicate registrations.
# Extend here for app-specific admin customizations.


class BookRequestAdmin(admin.ModelAdmin):
    list_display = ('user', 'request_type', 'title', 'status', 'created_date')
    list_filter = ('request_type', 'status')
    search_fields = ('title', 'user__username')