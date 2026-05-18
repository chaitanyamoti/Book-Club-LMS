from django.db.models.signals import post_save
from django.contrib.auth.models import User
from django.dispatch import receiver

from core.models import UserProfile
from notifications.models import EmailPreference


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """Create related user records whenever a new User is created."""
    if created:
        UserProfile.objects.create(user=instance)
        EmailPreference.objects.create(user=instance)


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    """Ensure the related UserProfile is saved when User is saved."""
    try:
        instance.userprofile.save()
    except UserProfile.DoesNotExist:
        # If profile doesn't exist, create it
        UserProfile.objects.create(user=instance)
