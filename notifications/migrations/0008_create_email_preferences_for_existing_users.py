from django.conf import settings
from django.db import migrations


def create_email_preferences(apps, schema_editor):
    user_model_label = settings.AUTH_USER_MODEL
    app_label, model_name = user_model_label.split('.')
    User = apps.get_model(app_label, model_name)
    EmailPreference = apps.get_model('notifications', 'EmailPreference')

    for user in User.objects.all():
        EmailPreference.objects.get_or_create(user=user)


class Migration(migrations.Migration):

    dependencies = [
        ('notifications', '0007_alter_emaillog_email_type'),
    ]

    operations = [
        migrations.RunPython(create_email_preferences, migrations.RunPython.noop),
    ]
