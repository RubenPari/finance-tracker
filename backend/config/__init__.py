"""Django project configuration package.

Initialises the Celery application instance so it is available
when Django starts, ensuring async task queues are ready.
"""
from .celery import app as celery_app

__all__ = ('celery_app',)
