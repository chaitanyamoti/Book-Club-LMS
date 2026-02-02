from core.models import ClubSettings

def get_club_setting(key, default):
    """
    Retrieves a setting from the ClubSettings model.
    Returns the setting_value or the default if the key is not found.
    """
    try:
        setting = ClubSettings.objects.get(setting_key=key)
        return setting.setting_value
    except ClubSettings.DoesNotExist:
        return str(default) # Ensure default is returned as string for consistency
