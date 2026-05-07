"""WSGI (Web Server Gateway Interface) configuration.

This module exposes the WSGI application callable that production
servers (e.g., Gunicorn, uWSGI) use to serve the Django application.
"""
import os
from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

application = get_wsgi_application()
