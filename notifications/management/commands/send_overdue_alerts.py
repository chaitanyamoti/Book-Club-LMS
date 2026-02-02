from django.core.management.base import BaseCommand
from notifications.utils import send_overdue_alerts


class Command(BaseCommand):
    help = 'Send overdue alert emails to users with overdue books'

    def handle(self, *args, **options):
        sent = send_overdue_alerts()
        self.stdout.write(self.style.SUCCESS(f'Sent {sent} overdue alert email(s)'))
