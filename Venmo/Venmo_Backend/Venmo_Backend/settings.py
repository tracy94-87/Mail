from pathlib import Path

from dotenv import dotenv_values, load_dotenv
import os

BASE_DIR = Path(__file__).resolve().parent.parent


def env(name: str, default: str = '') -> str:
    """
    Read config from the platform environment, falling back to .env when the
    platform value is missing or blank (Railway may register an empty var).
    """
    direct = os.environ.get(name)
    if direct is not None and str(direct).strip():
        return str(direct).strip()
    file_val = dotenv_values(BASE_DIR / '.env').get(name)
    if file_val is not None and str(file_val).strip():
        return str(file_val).strip()
    return default


load_dotenv(BASE_DIR / '.env', override=False)

SECRET_KEY = env('SECRET_KEY')

DEBUG = env('DEBUG', 'False') == 'True'

ALLOWED_HOSTS = ['*']

INSTALLED_APPS = [
    'django.contrib.staticfiles',
    'mailer',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'Venmo_Backend.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
            ],
        },
    },
]

WSGI_APPLICATION = 'Venmo_Backend.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    }
}

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# -----------------------------------------------------------------------------
# Email delivery
# - Railway Hobby: set RESEND_API_KEY (HTTPS API; SMTP ports are blocked)
# - Local dev: set EMAIL_HOST_PASSWORD for Hostinger SMTP, or RESEND_API_KEY
# -----------------------------------------------------------------------------
EMAIL_PROVIDER = env('EMAIL_PROVIDER', '')  # '', 'resend', or 'smtp'

RESEND_API_KEY = env('RESEND_API_KEY')
RESEND_FROM_EMAIL = env('RESEND_FROM_EMAIL', 'info@customerservice.click')

# Hostinger SMTP (local / Railway Pro only)
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.hostinger.com'
EMAIL_PORT = 465
EMAIL_USE_TLS = False
EMAIL_USE_SSL = True
EMAIL_HOST_USER = 'info@customerservice.click'
EMAIL_HOST_PASSWORD = env('EMAIL_HOST_PASSWORD')
EMAIL_TIMEOUT = int(env('EMAIL_TIMEOUT', '10'))

DEFAULT_FROM_EMAIL = RESEND_FROM_EMAIL or 'info@customerservice.click'
SERVER_EMAIL = DEFAULT_FROM_EMAIL

STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
