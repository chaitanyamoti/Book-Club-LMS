from django.db import migrations
import json
import os
from django.utils import timezone
from datetime import timedelta

def load_initial_data(apps, schema_editor):
    Book = apps.get_model('core', 'Book')
    User = apps.get_model('auth', 'User')
    UserProfile = apps.get_model('core', 'UserProfile')
    ClubSettings = apps.get_model('core', 'ClubSettings')
    Transaction = apps.get_model('core', 'Transaction')

    # 1. Initialize Club Settings
    default_settings = {
        'CLUB_NAME': 'Beyond the Pages',
        'LOAN_PERIOD_DAYS': '14',
        'RENEWAL_PERIOD_DAYS': '7',
        'MAX_RENEWALS_PER_LOAN': '2',
        'OVERDUE_FINE_PER_DAY': '0.50',
    }
    for key, value in default_settings.items():
        ClubSettings.objects.get_or_create(setting_key=key, defaults={'setting_value': value})

    # 2. Ensure Admin User exists
    admin_user, created = User.objects.get_or_create(
        username='admin',
        defaults={
            'email': 'admin@example.com',
            'is_staff': True,
            'is_superuser': True,
        }
    )
    if created:
        admin_user.set_password('AdminPass123')
        admin_user.save()
    
    UserProfile.objects.get_or_create(user=admin_user, defaults={'role': 'ADMIN'})

    # 3. Load Books from JSON
    # We use a hardcoded relative path from the project root
    file_path = 'sample_books.json'
    if not os.path.exists(file_path):
        return

    with open(file_path, 'r', encoding='utf-8') as f:
        data_rows = json.load(f)
    
    for row in data_rows:
        title = row.get('book name')
        author = row.get('author', 'Unknown')
        
        if not title:
            continue

        book, created = Book.objects.get_or_create(
            title=title,
            author=author,
            defaults={
                'added_by': admin_user,
                'total_copies': 1,
                'available_copies': 1,
                'status': 'AVAILABLE'
            }
        )
        
        # Handle sample transaction if employee name exists
        emp_name = row.get('employe name')
        if emp_name and str(emp_name).strip():
            emp_name_str = str(emp_name).strip()
            username = emp_name_str.lower().replace(' ', '_')
            
            member_user, _ = User.objects.get_or_create(
                username=username,
                defaults={'first_name': emp_name_str, 'email': f'{username}@example.com'}
            )
            UserProfile.objects.get_or_create(user=member_user, defaults={'role': 'MEMBER'})

            if book.available_copies > 0:
                due_date = timezone.now().date() + timedelta(days=14)
                Transaction.objects.get_or_create(
                    book=book,
                    user=member_user,
                    transaction_type='ISSUE',
                    return_date=None,
                    defaults={
                        'due_date': due_date,
                        'created_by': admin_user
                    }
                )
                book.available_copies = 0
                book.status = 'ISSUED'
                book.save()

class Migration(migrations.Migration):

    dependencies = [
        ('core', '0006_userprofile_account_activity_log_and_more'),
    ]

    operations = [
        migrations.RunPython(load_initial_data),
    ]
