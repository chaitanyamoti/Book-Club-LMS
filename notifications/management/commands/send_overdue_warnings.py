from django.core.management.base import BaseCommand, CommandError
from notifications.utils import send_overdue_alerts

class Command(BaseCommand):
    help = 'Finds all overdue book transactions and sends reminder emails to the users.'

    def handle(self, *args, **options):
        self.stdout.write('Starting to send overdue book warnings...')
        
        try:
            sent_count = send_overdue_alerts()
            self.stdout.write(self.style.SUCCESS(f'Successfully sent {sent_count} overdue warning email(s).'))
        except Exception as e:
            raise CommandError(f'An error occurred while sending emails: {e}')
