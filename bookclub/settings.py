import os
from pathlib import Path
from datetime import timedelta


BASE_DIR = Path(__file__).resolve().parent.parent

# ✅ LOAD .env FIRST
if (BASE_DIR / '.env').exists():
    try:
        from dotenv import load_dotenv
        result = load_dotenv(BASE_DIR / '.env')
        print(f"DEBUG: .env file exists at {BASE_DIR / '.env'}")
        print(f"DEBUG: load_dotenv result: {result}")
    except ImportError:
        print("WARNING: python-dotenv is not installed. Environment variables not loaded from .env file.")
    except Exception as e:
        print(f"WARNING: An error occurred while loading .env file: {e}")
else:
    print(f"DEBUG: .env file does not exist at {BASE_DIR / '.env'}")


SECRET_KEY = os.environ.get('SECRET_KEY', 'django-insecure-change-this-in-production')

DEBUG = os.environ.get('DEBUG', 'True') == 'True'

ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS', '*').split(',') if os.environ.get('ALLOWED_HOSTS') else ['*']  # For development, change for production

INSTALLED_APPS = [
    'jazzmin',  # MUST BE FIRST

    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Third party
    'crispy_forms',
    'crispy_bootstrap5',
    'import_export',

    # Our apps
    'core',
    'users',
    'books',
    'transactions',
    'reading',
    'bookrequests',
    'notifications',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'bookclub.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'core.context_processors.club_settings',
                'notifications.context_processors.notifications_context',
            ],
        },
    },
]

WSGI_APPLICATION = 'bookclub.wsgi.application'

# DATABASE - SQLite for dev, PostgreSQL for production
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# Update database configuration from DATABASE_URL environment variable
if os.environ.get('DATABASE_URL'):
    import dj_database_url
    DATABASES['default'] = dj_database_url.config(
        conn_max_age=600,
        ssl_require=True
    )

# CSRF Trusted Origins for Render
RENDER_EXTERNAL_HOSTNAME = os.environ.get('RENDER_EXTERNAL_HOSTNAME')
if RENDER_EXTERNAL_HOSTNAME:
    ALLOWED_HOSTS.append(RENDER_EXTERNAL_HOSTNAME)
    CSRF_TRUSTED_ORIGINS = [f"https://{RENDER_EXTERNAL_HOSTNAME}"]


AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Asia/Kolkata'
USE_I18N = True
USE_TZ = True

STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [BASE_DIR / 'static']

MEDIA_URL = 'media/'
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# LOGIN/LOGOUT URLs
LOGIN_URL = 'users:login'
LOGIN_REDIRECT_URL = '/dashboard/'
LOGOUT_REDIRECT_URL = '/'

# CRISPY FORMS
CRISPY_ALLOWED_TEMPLATE_PACKS = "bootstrap5"
CRISPY_TEMPLATE_PACK = "bootstrap5"

# =========================
# EMAIL CONFIG (SINGLE SOURCE OF TRUTH)
# =========================

# EMAIL_BACKEND_TYPE = os.environ.get("EMAIL_BACKEND_TYPE", "console").lower()

# DEFAULT_FROM_EMAIL = os.environ.get(
#     "DEFAULT_FROM_EMAIL",
#     "Book Club <noreply@bookclub.local>"
# )

# if EMAIL_BACKEND_TYPE == "smtp":
#     EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
#     EMAIL_HOST = os.environ.get("EMAIL_HOST", "smtp.gmail.com")
#     EMAIL_PORT = int(os.environ.get("EMAIL_PORT", "587"))
#     EMAIL_USE_TLS = os.environ.get("EMAIL_USE_TLS", "True") == "True"
#     EMAIL_HOST_USER = os.environ.get("EMAIL_HOST_USER")
#     EMAIL_HOST_PASSWORD = os.environ.get("EMAIL_HOST_PASSWORD")

# elif EMAIL_BACKEND_TYPE == "file":
#     EMAIL_BACKEND = "django.core.mail.backends.filebased.EmailBackend"
#     EMAIL_FILE_PATH = BASE_DIR / "sent_emails"

# else:
#     EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
# EMAIL CONFIGURATION
# For development, use console backend (emails printed to console)
# For production, set EMAIL_BACKEND_TYPE=smtp in environment variables with credentials
EMAIL_BACKEND_TYPE = os.environ.get("EMAIL_BACKEND_TYPE", "console").lower()

DEFAULT_FROM_EMAIL = os.environ.get(
    "DEFAULT_FROM_EMAIL",
    "Book Club <noreply@bookclub.local>"
)

if EMAIL_BACKEND_TYPE == "smtp":
    # Only use SMTP if credentials are provided
    EMAIL_HOST_USER = os.environ.get("EMAIL_HOST_USER")
    EMAIL_HOST_PASSWORD = os.environ.get("EMAIL_HOST_PASSWORD")

    if EMAIL_HOST_USER and EMAIL_HOST_PASSWORD:
        EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
        EMAIL_HOST = os.environ.get("EMAIL_HOST", "sandbox.smtp.mailtrap.io")
        EMAIL_PORT = int(os.environ.get("EMAIL_PORT", "587"))
        EMAIL_USE_TLS = os.environ.get("EMAIL_USE_TLS", "True") == "True"
        print("DEBUG: Using SMTP backend with credentials")
    else:
        print("WARNING: EMAIL_BACKEND_TYPE=smtp but no EMAIL_HOST_USER/EMAIL_HOST_PASSWORD found. Falling back to console backend.")
        EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

elif EMAIL_BACKEND_TYPE == "file":
    EMAIL_BACKEND = "django.core.mail.backends.filebased.EmailBackend"
    EMAIL_FILE_PATH = BASE_DIR / "sent_emails"

else:
    EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"


print("EMAIL_BACKEND =", EMAIL_BACKEND)


# Production Security Settings (HTTPS, HSTS, Cookies, CSP)
# These should generally only be active when DEBUG is False
if not DEBUG:
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_HSTS_SECONDS = 31536000  # 1 year
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True # Optional, but good for maximum security

    # Content Security Policy (CSP) - Implement carefully!
    # This is a very basic example. You will need to customize this
    # heavily based on all the external resources your site uses.
    # CSP should ideally be tested thoroughly in a staging environment.
    SECURE_CONTENT_SECURITY_POLICY = {
        "default-src": ("'self'",),
        "script-src": ("'self'", "https://cdn.jsdelivr.net"), # Add any CDN for JS, like Bootstrap's
        "style-src": ("'self'", "https://cdn.jsdelivr.net"), # Add any CDN for CSS
        "img-src": ("'self'", "data:",), # Allow data URIs for images
        "font-src": ("'self'", "https://cdn.jsdelivr.net"), # Add any CDN for fonts
        "connect-src": ("'self'",),
        "frame-ancestors": ("'self'",),
        "form-action": ("'self'",),
        "base-uri": ("'self'",),
        "object-src": ("'none'",),
        "script-src-attr": ("'none'",),
        "upgrade-insecure-requests": True,
    }


# JAZZMIN SETTINGS (Modern Admin Theme)
JAZZMIN_SETTINGS = {
    "site_title": "Beyond the Pages Admin",
    "site_header": "Beyond the Pages",
    "site_brand": "Beyond the Pages",
    "site_logo": "images/logo.png",
    "login_logo": "images/logo.png",
    "site_icon": "images/logo.png",
    "welcome_sign": "Welcome to Beyond the Pages Admin Panel",
    "copyright": "Beyond the Pages",
            "search_model": ["auth.User", "core.Book"],    "user_avatar": None,
    "topmenu_links": [
        {"name": "Dashboard", "url": "admin:index", "permissions": ["auth.view_user"]},
        {"name": "Home", "url": "core:home", "new_window": False},
    ],
    "usermenu_links": [
        {"model": "notifications.EmailLog"},
        {"model": "notifications.UserNotification"},
    ],
    "show_sidebar": True,
    "navigation_expanded": True,
    "hide_apps": [],
    "hide_models": [
        "core.UserProfile",
        "notifications.EmailLog",
        "notifications.UserNotification",
    ],
    "order_with_respect_to": ["auth", "core", "transactions", "reading", "bookrequests", "notifications", "users"],
    "apps": {
        "core": {
            "icon": "fas fa-book",
            "name": "Library Management",
        },
        "transactions": {
            "icon": "fas fa-exchange-alt",
            "name": "Book Transactions",
        },
        "reading": {
            "icon": "fas fa-book-reader",
            "name": "Reading Activities",
        },
        "bookrequests": {
            "icon": "fas fa-hand-paper",
            "name": "Book Requests",
        },
        "notifications": {
            "icon": "fas fa-bell",
            "name": "Notifications",
        },
        "users": {
            "icon": "fas fa-users",
            "name": "User Management",
        },
    },
    "icons": {
        "auth.User": "fas fa-user",
        "auth.Group": "fas fa-users",
        "core.Book": "fas fa-book",
        "core.Transaction": "fas fa-exchange-alt",
        "core.ReadingLog": "fas fa-calendar-check",
        "core.BookRequest": "fas fa-hand-paper",
        "core.UserProfile": "fas fa-id-card",
        "core.ClubSettings": "fas fa-cogs",
        "transactions.Transaction": "fas fa-exchange-alt",
        "reading.ReadingLog": "fas fa-calendar-check",
        "reading.ReadingChallenge": "fas fa-trophy",
        "reading.UserReadingChallenge": "fas fa-user-trophy",
        "reading.ReadingGroup": "fas fa-users",
        "reading.GroupMembership": "fas fa-user-plus",
        "bookrequests.BookRequest": "fas fa-hand-paper",
        "notifications.Announcement": "fas fa-bullhorn",
        "notifications.UserNotification": "fas fa-bell",
        "notifications.EmailPreference": "fas fa-envelope",
        "notifications.EmailLog": "fas fa-mail-bulk",
    },
    "default_icon_parents": "fas fa-chevron-circle-right",
    "default_icon_children": "fas fa-circle",
    "related_modal_active": True,
    "custom_css": "css/admin.css",
    "custom_js": "js/admin.js",
    "show_ui_builder": False,
    "changeform_format": "horizontal_tabs",
    "changeform_format_overrides": {"auth.user": "collapsible", "auth.group": "vertical_tabs"},
}
print("EMAIL_BACKEND_TYPE =", os.environ.get("EMAIL_BACKEND_TYPE"))
print("EMAIL_BACKEND =", EMAIL_BACKEND)
