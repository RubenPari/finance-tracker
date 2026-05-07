"""Django project settings for the Finance Tracker application.

Configures the database (PostgreSQL), installed apps, middleware,
REST Framework, JWT authentication, CORS, Celery task queue,
AI gateway integration, and all other Django/DRF settings.

Sensitive values (SECRET_KEY, DB credentials) are read from
environment variables with development defaults.
"""
import os
from pathlib import Path

# ---------------------------------------------------------------------------
# Base directory: parent of this settings file (the backend/ directory)
# ---------------------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent.parent

# ---------------------------------------------------------------------------
# Security: secret key and debug mode
# ---------------------------------------------------------------------------
# Never commit a real SECRET_KEY to version control.
SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY', 'dev-secret-change-me')

# DEBUG should be False in production.
DEBUG = os.environ.get('DJANGO_DEBUG', 'true').lower() == 'true'

# Comma-separated list of allowed hostnames for request validation.
ALLOWED_HOSTS = os.environ.get('DJANGO_ALLOWED_HOSTS', 'localhost,127.0.0.1').split(',')

# ---------------------------------------------------------------------------
# Installed applications
# ---------------------------------------------------------------------------
INSTALLED_APPS = [
    # Django built-in apps
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # Third-party apps
    'rest_framework',
    'rest_framework_simplejwt',
    'rest_framework_simplejwt.token_blacklist',
    'corsheaders',
    'django_filters',
    # Local apps (finance tracker business logic)
    'apps.authentication',
    'apps.transactions',
    'apps.categories',
    'apps.budgets',
    'apps.stats',
    'apps.suggestions',
]

# ---------------------------------------------------------------------------
# Middleware stack (order matters: request flows top-to-bottom, response bottom-to-top)
# ---------------------------------------------------------------------------
MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',       # Must be first to handle CORS headers
    'django.middleware.security.SecurityMiddleware',  # Security enhancements (HSTS, etc.)
    'django.contrib.sessions.middleware.SessionMiddleware',  # Session management
    'django.middleware.common.CommonMiddleware',    # Common utilities (trailing slashes, etc.)
    'django.middleware.csrf.CsrfViewMiddleware',    # CSRF token protection
    'django.contrib.auth.middleware.AuthenticationMiddleware',  # User authentication
    'django.contrib.messages.middleware.MessageMiddleware',  # Flash messaging
    'django.middleware.clickjacking.XFrameOptionsMiddleware',  # Clickjacking protection
]

# Root URL configuration module
ROOT_URLCONF = 'config.urls'

# ---------------------------------------------------------------------------
# Template configuration
# ---------------------------------------------------------------------------
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
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

# WSGI application entry point for production servers (e.g., Gunicorn)
WSGI_APPLICATION = 'config.wsgi.application'

# ---------------------------------------------------------------------------
# Database: PostgreSQL via environment variables
# ---------------------------------------------------------------------------
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ.get('DB_NAME', 'finance_tracker'),
        'USER': os.environ.get('DB_USER', 'postgres'),
        'PASSWORD': os.environ.get('DB_PASSWORD', 'postgres'),
        'HOST': os.environ.get('DB_HOST', 'localhost'),
        'PORT': os.environ.get('DB_PORT', '5432'),
    }
}

# ---------------------------------------------------------------------------
# Password validation rules
# ---------------------------------------------------------------------------
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# ---------------------------------------------------------------------------
# Internationalization and time zone
# ---------------------------------------------------------------------------
LANGUAGE_CODE = 'it'
TIME_ZONE = 'Europe/Rome'
USE_I18N = True
USE_TZ = True

# Static files URL prefix
STATIC_URL = 'static/'

# Default primary key field type for new models
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ---------------------------------------------------------------------------
# CORS configuration: allow frontend development server
# ---------------------------------------------------------------------------
CORS_ALLOWED_ORIGINS = [
    'http://localhost:5173',
    'http://127.0.0.1:5173',
]
CORS_ALLOW_CREDENTIALS = True

# ---------------------------------------------------------------------------
# Django REST Framework configuration
# ---------------------------------------------------------------------------
REST_FRAMEWORK = {
    # Use JWT tokens for authentication
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    # Require authentication for all endpoints by default
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
    # Enable pagination (50 items per page)
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 50,
    # Enable filtering, searching, and ordering on viewsets
    'DEFAULT_FILTER_BACKENDS': (
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ),
}

# ---------------------------------------------------------------------------
# Simple JWT: token lifetime and rotation settings
# ---------------------------------------------------------------------------
from datetime import timedelta

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(hours=1),       # Access tokens expire after 1 hour
    'REFRESH_TOKEN_LIFETIME': timedelta(days=30),       # Refresh tokens last 30 days
    'ROTATE_REFRESH_TOKENS': True,                      # Issue new refresh token on each refresh
    'BLACKLIST_AFTER_ROTATION': True,                   # Blacklist old refresh tokens
    'AUTH_HEADER_TYPES': ('Bearer',),                   # Expected Authorization header prefix
}

# ---------------------------------------------------------------------------
# Celery: asynchronous task queue via Redis
# ---------------------------------------------------------------------------
CELERY_BROKER_URL = os.environ.get('CELERY_BROKER_URL', 'redis://localhost:6379/0')
CELERY_RESULT_BACKEND = os.environ.get('CELERY_RESULT_BACKEND', 'redis://localhost:6379/0')
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = 'Europe/Rome'

# ---------------------------------------------------------------------------
# AI Gateway configuration for transaction suggestions
# ---------------------------------------------------------------------------
AI_GATEWAY_URL = os.environ.get(
    'AI_GATEWAY_URL', 'https://ai-gateway.vercel.sh/v1/chat/completions'
)
AI_GATEWAY_KEY = os.environ.get('AI_GATEWAY_KEY', '')
if not AI_GATEWAY_KEY:
    raise ValueError(
        "AI_GATEWAY_KEY is required but not set. "
        "Add it to your .env file to start the application."
    )
AI_GATEWAY_MODEL = os.environ.get('AI_GATEWAY_MODEL', 'xai/grok-4.1-fast-non-reasoning')
AI_SUGGESTIONS_TIMEOUT = int(os.environ.get('AI_SUGGESTIONS_TIMEOUT', '10'))

# ---------------------------------------------------------------------------
# AI Gateway configuration for transaction auto-categorization
# ---------------------------------------------------------------------------
AI_CATEGORIZATION_ENABLED = os.environ.get('AI_CATEGORIZATION_ENABLED', 'true').lower() == 'true'
AI_CATEGORIZATION_BATCH_SIZE = int(os.environ.get('AI_CATEGORIZATION_BATCH_SIZE', '20'))
AI_CATEGORIZATION_TIMEOUT = int(os.environ.get('AI_CATEGORIZATION_TIMEOUT', '15'))
AI_CATEGORIZATION_CACHE_TTL = int(os.environ.get('AI_CATEGORIZATION_CACHE_TTL', '2592000'))  # 30 days

# ---------------------------------------------------------------------------
# Custom user model
# ---------------------------------------------------------------------------
AUTH_USER_MODEL = 'authentication.User'
