"""ASGI (Asynchronous Server Gateway Interface) configuration.

This module exposes the ASGI application callable for async-capable
servers (e.g., Daphne, Uvicorn). Required for Django's async features
and WebSocket support.
"""
import os
from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

application = get_asgi_application()
