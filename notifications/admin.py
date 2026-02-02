from django.contrib import admin
from django.urls import path # Import path for custom admin URLs
from django.template.response import TemplateResponse # For rendering custom admin templates
from django.db.models import Count, Q # For aggregation and complex queries
from .models import Announcement, UserNotification, EmailLog # Import all models needed

@admin.register(Announcement)
class AnnouncementAdmin(admin.ModelAdmin):
    list_display = ('title', 'pub_date', 'is_active', 'display_on_homepage')
    list_filter = ('is_active', 'display_on_homepage', 'pub_date')
    search_fields = ('title', 'content')

@admin.register(UserNotification)
class UserNotificationAdmin(admin.ModelAdmin):
    list_display = ('user', 'message', 'created_at', 'is_read', 'type', 'link_url')
    list_filter = ('is_read', 'type', 'created_at')
    search_fields = ('user__username', 'message')
    fields = ('user', 'message', 'is_read', 'link_url', 'type')

@admin.register(EmailLog)
class EmailLogAdmin(admin.ModelAdmin):
    list_display = ('user', 'email_type', 'subject', 'recipient', 'status', 'sent_at', 'created_at', 'opened_at', 'ab_test_variant', 'campaign_id')
    list_filter = ('email_type', 'status', 'ab_test_variant', 'sent_at', 'created_at')
    search_fields = ('user__username', 'recipient', 'subject', 'campaign_id')
    readonly_fields = ('user', 'email_type', 'subject', 'recipient', 'status', 'error_message', 'sent_at', 'created_at', 'email_content', 'opened_at', 'clicked_links', 'user_agent', 'ip_address', 'ab_test_variant', 'campaign_id')
    fields = ('user', 'email_type', 'subject', 'recipient', 'status', 'error_message', 'sent_at', 'created_at', 'email_content', 'opened_at', 'clicked_links', 'user_agent', 'ip_address', 'ab_test_variant', 'campaign_id')

    def get_urls(self):
        urls = super().get_urls()
        my_urls = [
            path('analytics/', self.admin_site.admin_view(self.email_analytics_view), name='email_analytics'),
        ]
        return my_urls + urls

    def email_analytics_view(self, request):
        # Overall Stats
        total_emails_sent = EmailLog.objects.filter(status='SENT').count()
        total_emails_opened = EmailLog.objects.filter(opened_at__isnull=False).count()
        overall_open_rate = (total_emails_opened / total_emails_sent * 100) if total_emails_sent > 0 else 0

        # Analytics by Email Type
        analytics_by_type = EmailLog.objects.values('email_type').annotate(
            sent_count=Count('pk', filter=Q(status='SENT')),
            opened_count=Count('pk', filter=Q(status='SENT', opened_at__isnull=False))
        ).order_by('email_type')
        
        for item in analytics_by_type:
            item['open_rate'] = (item['opened_count'] / item['sent_count'] * 100) if item['sent_count'] > 0 else 0

        # Analytics by A/B Test Variant
        analytics_by_variant = EmailLog.objects.values('campaign_id', 'ab_test_variant').annotate(
            sent_count=Count('pk', filter=Q(status='SENT')),
            opened_count=Count('pk', filter=Q(status='SENT', opened_at__isnull=False))
        ).order_by('campaign_id', 'ab_test_variant')

        for item in analytics_by_variant:
            item['open_rate'] = (item['opened_count'] / item['sent_count'] * 100) if item['sent_count'] > 0 else 0


        context = dict(
            self.admin_site.each_context(request),
            title="Email Analytics Dashboard",
            total_emails_sent=total_emails_sent,
            total_emails_opened=total_emails_opened,
            overall_open_rate=f"{overall_open_rate:.2f}",
            analytics_by_type=analytics_by_type,
            analytics_by_variant=analytics_by_variant,
        )
        return TemplateResponse(request, "notifications/admin/email_analytics.html", context)
