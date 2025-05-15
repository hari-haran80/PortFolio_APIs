from pathlib import Path
import os

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-mq7tmk+eg+jh=rr%u*mzc8#6aa3pjo8tnlueyn5r+g_m=m_jq+'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ["*"]

FRONTEND_URL = "http://localhost:3000"
# Application definition

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
}

# Email settings
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_HOST_USER = 'hariharan.a69@gmail.com'
EMAIL_HOST_PASSWORD = 'lyrv ekne vwmf luzo'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
DEFAULT_FROM_EMAIL = 'hariharan.a69@gmail.com'  # Should match EMAIL_HOST_USER
ADMIN_EMAIL = 'hariharan.a6998@gmail.com'  # For admin notifications

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

# default Enging

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / "db.sqlite3",
    }
}


# freeDB Database

# https://docs.djangoproject.com/en/5.2/ref/settings/#databases

# DATABASES = {
#     'default': {
#         'ENGINE': 'django.db.backends.mysql',
#         'NAME': 'freedb_Hari_DB',
#         'USER': 'freedb_Hariharan',
#         'PASSWORD': 'a&k8pqyxVzK2CRF',
#         'HOST': 'sql.freedb.tech',
#         'PORT': '3306',
#         'OPTIONS': {
#             'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
#             'charset': 'utf8mb4',
#         },
#     }
# }

# railway DataBase

# DATABASES = {
#     'default': {
#         'ENGINE': 'django.db.backends.mysql',
#         'NAME': 'railway',
#         'USER': 'root',
#         'PASSWORD': 'FhDgShlRLakunNISVohouwuHMthAMREr',
#         'HOST': 'hopper.proxy.rlwy.net',
#         'PORT': 26738,
#         'OPTIONS': {
#             'charset': 'utf8mb4',
#             'ssl_mode': 'REQUIRED',  # Railway enforces SSL
#         },
#     }
# }

# AWS Database
# SESSION_ENGINE = "django.contrib.sessions.backends.cached_db"  # Correct for memory optimization

# DATABASES = {
#     'default': {
#         'ENGINE': 'django.db.backends.mysql',
#         'NAME': 'Portfolio_DB',
#         'USER': 'admin',
#         'PASSWORD': 'Hariharan80$',
#         'HOST': 'hari-db.cq3imwemgk2k.us-east-1.rds.amazonaws.com',
#         'PORT': '3306',
#         'OPTIONS': {
#             'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
#             'connect_timeout': 30,  # ← **Critical for Render free tier** (prevents hangs)
#         },
#         'CONN_MAX_AGE': 300,  # ← Moved outside 'OPTIONS' (was nested incorrectly)
#     }
# }

# Password validation
# https://docs.djangoproject.com/en/5.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/5.2/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.2/howto/static-files/

CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "https://3d10c0bt-3000.inc1.devtunnels.ms",

]

CORS_ALLOW_ALL_ORIGINS = True

# settings.py (add these at the bottom)
GITHUB_TOKEN = "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"
GITHUB_USERNAME = "hari-haran80"

STATIC_URL = 'static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# Default primary key field type
# https://docs.djangoproject.com/en/5.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

ENCRYPTION_KEY = b'neqyoFnUFgBzMzjPHDxSQ_-qXVRUxBnZDhf2aGnfHUU='
