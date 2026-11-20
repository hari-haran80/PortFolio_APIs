"""
Django settings for PortFolio_BE.

All secrets and environment-specific values are read from environment
variables. For local development, put them in a `.env` file next to
manage.py (see `.env.example`). Never commit real secrets to git.
"""
from pathlib import Path
import os
import sys

import cloudinary

BASE_DIR = Path(__file__).resolve().parent.parent


def _load_dotenv(path):
    """Minimal .env loader (KEY=VALUE per line) so no extra dependency is needed.
    Values already present in the real environment take precedence."""
    if not path.exists():
        return
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key, value = key.strip(), value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
            value = value[1:-1]
        os.environ.setdefault(key, value)


_load_dotenv(BASE_DIR / ".env")


def env(name, default=None):
    return os.environ.get(name, default)


def env_bool(name, default=False):
    value = os.environ.get(name)
    if value is None:
        return default
    return value.strip().lower() in ("1", "true", "yes", "on")


def env_list(name, default=""):
    return [item.strip() for item in os.environ.get(name, default).split(",") if item.strip()]


TESTING = "test" in sys.argv

# ---------------------------------------------------------------------------
# Core
# ---------------------------------------------------------------------------
DEBUG = env_bool("DJANGO_DEBUG", False)

SECRET_KEY = env("DJANGO_SECRET_KEY")
if not SECRET_KEY:
    if DEBUG or TESTING:
        SECRET_KEY = "django-insecure-local-dev-only-key-change-me"
    else:
        raise RuntimeError("DJANGO_SECRET_KEY environment variable is required when DEBUG is off.")

ALLOWED_HOSTS = env_list("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1,.onrender.com")

# Used to build links in emails (e.g. password reset). The FE uses a hash router.
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
    # Safe default: anything not explicitly opened up is read-only for the public.
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticatedOrReadOnly',
    ),
    'DEFAULT_THROTTLE_RATES': {
        'auth': '20/hour',
        'contact': '10/hour',
    },
}

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

# ---------------------------------------------------------------------------
# Database: set DATABASE_URL (postgres://..., mysql://...) to use a hosted DB.
# Falls back to the local SQLite file.
# ---------------------------------------------------------------------------
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

# ---------------------------------------------------------------------------
# Email
# ---------------------------------------------------------------------------
EMAIL_HOST = env("EMAIL_HOST", "smtp.gmail.com")
EMAIL_PORT = int(env("EMAIL_PORT", "587"))
EMAIL_USE_TLS = env_bool("EMAIL_USE_TLS", True)
EMAIL_HOST_USER = env("EMAIL_HOST_USER", "")
EMAIL_HOST_PASSWORD = env("EMAIL_HOST_PASSWORD", "")
EMAIL_TIMEOUT = 15
DEFAULT_FROM_EMAIL = env("DEFAULT_FROM_EMAIL", EMAIL_HOST_USER or "webmaster@localhost")
ADMIN_EMAIL = env("ADMIN_EMAIL", DEFAULT_FROM_EMAIL)
if EMAIL_HOST_USER and EMAIL_HOST_PASSWORD:
    EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
else:
    # No SMTP credentials configured: print emails to the console instead of crashing.
    EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# ---------------------------------------------------------------------------
# CORS / CSRF
# ---------------------------------------------------------------------------
CORS_ALLOWED_ORIGINS = env_list(
    "CORS_ALLOWED_ORIGINS",
    "http://localhost:3000,http://127.0.0.1:3000,https://react-portfolio-new-y91w.onrender.com",
)
CORS_ALLOW_ALL_ORIGINS = env_bool("CORS_ALLOW_ALL_ORIGINS", False)
CSRF_TRUSTED_ORIGINS = env_list("CSRF_TRUSTED_ORIGINS", "https://*.onrender.com")

# ---------------------------------------------------------------------------
# GitHub (used by /about/total-commits/)
# ---------------------------------------------------------------------------
GITHUB_TOKEN = env("GITHUB_TOKEN", "")
GITHUB_USERNAME = env("GITHUB_USERNAME", "hari-haran80")

# ---------------------------------------------------------------------------
# Static & media
# ---------------------------------------------------------------------------
STATIC_URL = 'static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# Django 5.1+ ignores the old STATICFILES_STORAGE / DEFAULT_FILE_STORAGE settings,
# so storage backends must be declared here.
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {
        "BACKEND": (
            "django.contrib.staticfiles.storage.StaticFilesStorage"
            if DEBUG or TESTING
            else "whitenoise.storage.CompressedManifestStaticFilesStorage"
        )
    },
}

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ---------------------------------------------------------------------------
# Cloudinary (profile pictures, project and skill images)
# ---------------------------------------------------------------------------
CLOUDINARY_STORAGE = {
    # The cloud name is public (it appears in every image URL) and is all that is
    # needed to *display* images. Uploads additionally need the key and secret.
    'CLOUD_NAME': env("CLOUDINARY_CLOUD_NAME", "dpxspxtpz"),
    'API_KEY': env("CLOUDINARY_API_KEY", ""),
    'API_SECRET': env("CLOUDINARY_API_SECRET", ""),
}
cloudinary.config(
    cloud_name=CLOUDINARY_STORAGE['CLOUD_NAME'],
    api_key=CLOUDINARY_STORAGE['API_KEY'],
    api_secret=CLOUDINARY_STORAGE['API_SECRET'],
    secure=True,
)

DEFAULT_PROFILE_PICTURE_URL = env(
    "DEFAULT_PROFILE_PICTURE_URL",
    "https://res.cloudinary.com/dpxspxtpz/image/upload/v1751656732/profile_l1prwv.png",
)

# Password reset links expire after this many minutes.
PASSWORD_RESET_TOKEN_TTL_MINUTES = int(env("PASSWORD_RESET_TOKEN_TTL_MINUTES", "60"))

# ---------------------------------------------------------------------------
# Production hardening (only when DEBUG is off)
# ---------------------------------------------------------------------------
if not DEBUG and not TESTING:
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_CONTENT_TYPE_NOSNIFF = True

if TESTING:
    PASSWORD_HASHERS = ['django.contrib.auth.hashers.MD5PasswordHasher']
    EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'
    CACHES = {'default': {'BACKEND': 'django.core.cache.backends.locmem.LocMemCache'}}
    REST_FRAMEWORK['DEFAULT_THROTTLE_RATES'] = {'auth': '10000/hour', 'contact': '10000/hour'}
