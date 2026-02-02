from .models import ClubSettings
from django.utils import timezone


def club_settings(request):
    """Context processor to add club settings to all templates"""
    settings = {}
    club_settings_objs = ClubSettings.objects.all()

    # Default values
    settings.update({
        'club_name': 'Company Book Club',
        'issuance_period': 30,  # days
        'max_renewals': 2,
        'current_year': timezone.now().year,
    })

    # Override with database values
    for setting in club_settings_objs:
        settings[setting.setting_key] = setting.setting_value

    return settings
