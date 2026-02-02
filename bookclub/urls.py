"""
URL configuration for bookclub project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth.decorators import user_passes_test
from django.shortcuts import redirect

# Store the original admin login view
original_admin_login = admin.site.login

def admin_login_redirect(request):
    """Redirect authenticated non-staff users away from admin login"""
    if request.user.is_authenticated and not request.user.is_staff:
        return redirect('core:dashboard')
    # Call the original login view
    return original_admin_login(request)

# Override admin login view
admin.site.login = admin_login_redirect

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('core.urls', namespace='core')),
    path('users/', include('users.urls', namespace='users')),
    path('books/', include('books.urls', namespace='books')),
    path('transactions/', include('transactions.urls', namespace='transactions')),
    path('reading/', include('reading.urls', namespace='reading')),
    path('requests/', include('bookrequests.urls', namespace='bookrequests')),
    path('notifications/', include('notifications.urls', namespace='notifications')),
    path('accounts/', include('django.contrib.auth.urls')),
]

# Serve static and media in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
