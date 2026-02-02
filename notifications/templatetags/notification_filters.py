from django import template
import base64

register = template.Library()

@register.simple_tag
def trackable_url(email_log_uuid, url):
    """
    Generates a trackable URL for email link clicks.
    """
    if not url:
        return ""
    
    redirect_url_base64 = base64.urlsafe_b64encode(url.encode('utf-8')).decode('utf-8')
    
    from django.urls import reverse
    try:
        return reverse('notifications:track_click', args=[email_log_uuid, redirect_url_base64])
    except:
        # Fallback for cases where reverse fails (e.g. during template rendering tests)
        return f"/notifications/track-click/{email_log_uuid}/{redirect_url_base64}/"
