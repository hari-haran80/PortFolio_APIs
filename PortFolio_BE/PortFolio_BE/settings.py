"""
Django settings for PortFolio_BE.

Every credential and environment-specific value comes from environment
variables. They are loaded from a `.env` file next to manage.py (local) or
from Render's secret file at /etc/secrets/.env. Real environment variables
always win over the files. Nothing secret is hardcoded here.
"""
import os
import sys
from pathlib import Path

import cloudinary

BASE_DIR = Path(__file__).resolve().parent.parent


def _load_env_file(path):
    """Minimal KEY=VALUE loader so no extra dependency is needed."""
    try:
        text = Path(path).read_text(encoding="utf-8")
    except (FileNotFoundError, PermissionError, OSError):
        return
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key, value = key.strip(), value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
            value = value[1:-1]
        os.environ.setdefault(key, value)


_load_env_file(BASE_DIR / ".env")
_load_env_file("/etc/secrets/.env")  # Render "Secret Files"


def env(name, default=""):
    return os.environ.get(name, default)


def env_bool(name, default=False):
    value = os.environ.get(name)
    if value is None or value.strip() == "":
        return default
    return value.strip().lower() in ("1", "true", "yes", "on")


def env_list(name, default=""):
    return [item.strip() for item in env(name, default).split(",") if item.strip()]


TESTING = len(sys.argv) > 1 and sys.argv[1] == "test"

# -----------------------------------------------------------------------------
# Core
# -----------------------------------------------------------------------------
DEBUG = env_bool("DJANGO_DEBUG", False)

SECRET_KEY = env("DJANGO_SECRET_KEY")
if not SECRET_KEY:
    if DEBUG or TESTING:
        SECRET_KEY = "django-insecure-local-only-not-for-production"
    else:
        raise RuntimeError(
            "DJANGO_SECRET_KEY is not set. Create PortFolio_BE/.env (see .env.example) "
            "or add it in Render -> Environment."
        )

ALLOWED_HOSTS = env_list("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1,.onrender.com")
ENCRYPTION_KEY = env("ENCRYPTION_KEY").encode() or None

# Used to build links in emails (e.g. password reset).
FRONTEND_URL = env("FRONTEND_URL", "http://localhost:3000").rstrip("/")

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'rest_framework',
    'rest_framework.authtoken',
    'rest_framework_simplejwt.token_blacklist',
    'corsheaders',
    'cloudinary',
    'cloudinary_storage',
    'django.contrib.staticfiles',
    'Apps.Authentication_App',
    'Apps.Profile_App',
    'Apps.Contact_App',
    'Apps.Projects_app',
    'Apps.Resume_app',
    'Apps.Review_app',
    'Apps.Skills_app',
    'Apps.Theme_app',
    'Apps.About_app',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    # Anything not explicitly opened up is read-only for the public.
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticatedOrReadOnly',
    ),
    # Used by the login/register/password-reset and contact endpoints.
    'DEFAULT_THROTTLE_RATES': {
        'auth': '20/hour',
        'contact': '10/hour',
    },
}

# Password reset links expire after this many minutes.
PASSWORD_RESET_TOKEN_TTL_MINUTES = int(env("PASSWORD_RESET_TOKEN_TTL_MINUTES", "60"))

ROOT_URLCONF = 'PortFolio_BE.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'PortFolio_BE.wsgi.application'

# -----------------------------------------------------------------------------
# Database: DATABASE_URL (postgres://..., mysql://...) or the local SQLite file.
# -----------------------------------------------------------------------------
DATABASE_URL = env("DATABASE_URL")
if DATABASE_URL and not TESTING:
    import dj_database_url
    DATABASES = {'default': dj_database_url.parse(DATABASE_URL, conn_max_age=300)}
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / "db.sqlite3",
        }
    }

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# -----------------------------------------------------------------------------
# Email: Brevo HTTPS API when BREVO_API_KEY is set, otherwise SMTP (Gmail).
# Without either, emails are printed to the console so nothing crashes.
# -----------------------------------------------------------------------------
BREVO_API_KEY = env("BREVO_API_KEY")
EMAIL_HOST = env("EMAIL_HOST", "smtp.gmail.com")
EMAIL_PORT = int(env("EMAIL_PORT", "587"))
EMAIL_USE_TLS = env_bool("EMAIL_USE_TLS", True)
EMAIL_HOST_USER = env("EMAIL_HOST_USER")
EMAIL_HOST_PASSWORD = env("EMAIL_HOST_PASSWORD")
EMAIL_TIMEOUT = 15
DEFAULT_FROM_EMAIL = env("DEFAULT_FROM_EMAIL", EMAIL_HOST_USER or "webmaster@localhost")
DEFAULT_FROM_NAME = env("DEFAULT_FROM_NAME", "Portfolio")
ADMIN_EMAIL = env("ADMIN_EMAIL", DEFAULT_FROM_EMAIL)

if BREVO_API_KEY:
    EMAIL_BACKEND = 'Apps.Contact_App.email_backends.BrevoEmailBackend'
elif EMAIL_HOST_USER and EMAIL_HOST_PASSWORD:
    EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
else:
    EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# -----------------------------------------------------------------------------
# CORS / CSRF
# -----------------------------------------------------------------------------
CORS_ALLOWED_ORIGINS = env_list(
    "CORS_ALLOWED_ORIGINS",
    "http://localhost:3000,http://127.0.0.1:3000,https://react-portfolio-new-y91w.onrender.com",
)
CORS_ALLOW_ALL_ORIGINS = env_bool("CORS_ALLOW_ALL_ORIGINS", False)
CSRF_TRUSTED_ORIGINS = env_list("CSRF_TRUSTED_ORIGINS", "https://*.onrender.com")

# -----------------------------------------------------------------------------
# GitHub (About page commit counter)
# -----------------------------------------------------------------------------
GITHUB_TOKEN = env("GITHUB_TOKEN")
GITHUB_USERNAME = env("GITHUB_USERNAME", "hari-haran80")

# -----------------------------------------------------------------------------
# Static & media
# -----------------------------------------------------------------------------
STATIC_URL = 'static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# Django 5.1+ ignores STATICFILES_STORAGE / DEFAULT_FILE_STORAGE; use STORAGES.
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    # Non-manifest WhiteNoise storage: works with the committed staticfiles/
    # folder even if collectstatic is not run on deploy.
    "staticfiles": {"BACKEND": "whitenoise.storage.CompressedStaticFilesStorage"},
}

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# -----------------------------------------------------------------------------
# Cloudinary (profile pictures, project and skill images)
# -----------------------------------------------------------------------------
CLOUDINARY_STORAGE = {
    'CLOUD_NAME': env("CLOUDINARY_CLOUD_NAME"),
    'API_KEY': env("CLOUDINARY_API_KEY"),
    'API_SECRET': env("CLOUDINARY_API_SECRET"),
}
cloudinary.config(
    cloud_name=CLOUDINARY_STORAGE['CLOUD_NAME'] or None,
    api_key=CLOUDINARY_STORAGE['API_KEY'] or None,
    api_secret=CLOUDINARY_STORAGE['API_SECRET'] or None,
    secure=True,
)

# Public image URL (not a secret). It is also a model field default, so it keeps
# a fixed fallback to avoid spurious migrations.
DEFAULT_PROFILE_PICTURE_URL = env(
    "DEFAULT_PROFILE_PICTURE_URL",
    "https://res.cloudinary.com/dpxspxtpz/image/upload/v1751656732/profile_l1prwv.png",
)

# -----------------------------------------------------------------------------
# Production hardening (DEBUG off)
# -----------------------------------------------------------------------------
if not DEBUG and not TESTING:
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    X_FRAME_OPTIONS = 'DENY'

# -----------------------------------------------------------------------------
# Test-only overrides: no real emails, no external services, no throttling.
# -----------------------------------------------------------------------------
if TESTING:
    PASSWORD_HASHERS = ['django.contrib.auth.hashers.MD5PasswordHasher']
    EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'
    REST_FRAMEWORK['DEFAULT_THROTTLE_RATES'] = {'auth': '10000/hour', 'contact': '10000/hour'}
    CACHES = {'default': {'BACKEND': 'django.core.cache.backends.locmem.LocMemCache'}}
    CLOUDINARY_STORAGE['CLOUD_NAME'] = CLOUDINARY_STORAGE['CLOUD_NAME'] or 'test-cloud'
    cloudinary.config(cloud_name=CLOUDINARY_STORAGE['CLOUD_NAME'])
