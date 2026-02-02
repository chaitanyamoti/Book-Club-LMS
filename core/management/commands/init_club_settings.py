from django.core.management.base import BaseCommand
from core.models import ClubSettings

class Command(BaseCommand):
    help = 'Initializes the application with default club settings if they do not exist.'

    def handle(self, *args, **options):
        self.stdout.write('Initializing club settings...')

        default_settings = {
            'CLUB_NAME': {'value': 'My Book Club', 'desc': 'The public name of the book club.'},
            'LOAN_PERIOD_DAYS': {'value': '14', 'desc': 'The number of days a book can be borrowed before it is overdue.'},
            'RENEWAL_PERIOD_DAYS': {'value': '7', 'desc': 'The number of extra days granted when a loan is renewed.'},
            'MAX_RENEWALS_PER_LOAN': {'value': '2', 'desc': 'The maximum number of times a single book loan can be renewed.'},
            'OVERDUE_FINE_PER_DAY': {'value': '0.25', 'desc': 'The fine amount (in local currency) charged per day for an overdue book.'},
        }

        created_count = 0
        for key, details in default_settings.items():
            obj, created = ClubSettings.objects.get_or_create(
                setting_key=key,
                defaults={'setting_value': details['value'], 'description': details['desc']}
            )
            if created:
                self.stdout.write(f'  Created setting: {key} = {details["value"]}')
                created_count += 1

        if created_count == 0:
            self.stdout.write(self.style.SUCCESS('All default settings already exist. No changes made.'))
        else:
            self.stdout.write(self.style.SUCCESS(f'Successfully created {created_count} new setting(s).'))
