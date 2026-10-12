"""
Django settings for MAIN project.
"""

from pathlib import Path
import os

# Build paths inside the project
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY', 'django-insecure-dev-key')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

# ALLOWED_HOSTS = ['hiceteacherevaluation.pythonanywhere.com']
ALLOWED_HOSTS = ["*"]

LOGIN_URL = 'admin_login'

# ==========================
# Email Configuration (Gmail TLS)
# ==========================
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_USE_SSL = False  # TLS and SSL cannot be True at the same time
EMAIL_HOST_USER = os.environ.get('GMAIL_USER', 'hicevaluation@gmail.com')
EMAIL_HOST_PASSWORD = os.environ.get('GMAIL_APP_PASSWORD', 'YOUR_APP_PASSWORD')  # 16-char App Password
DEFAULT_FROM_EMAIL = EMAIL_HOST_USER

# ==========================
# Installed Applications
# ==========================
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.humanize',
    'django.contrib.staticfiles',
    'evaluation',
]

# ==========================
# Middleware
# ==========================
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'MAIN.urls'

USE_TZ = True
TIME_ZONE = 'Asia/Manila'

# ==========================
# Templates
# ==========================
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
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

WSGI_APPLICATION = 'MAIN.wsgi.application'

# ==========================
# Database
# ==========================
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# DATABASES = {
#     'default': {
#         'ENGINE': 'django.db.backends.mysql',
#         'NAME': 'HIC_EVALUATION',   # your database name
#         'USER': 'root',                    # your MySQL username
#         'PASSWORD': 'shyle@03092021',       # your MySQL password
#         'HOST': 'localhost',               # or your DB server IP
#         'PORT': '3306',                    # default MySQL port
#     }
# }

# ==========================
# Password Validation
# ==========================
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# ==========================
# Internationalization
# ==========================
LANGUAGE_CODE = 'en-us'
USE_I18N = True
USE_TZ = True

# ==========================
# Static Files
# ==========================
STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / "static"]

STATIC_ROOT = BASE_DIR / 'staticfiles'

# ==========================
# Default Primary Key Field
# ==========================
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'