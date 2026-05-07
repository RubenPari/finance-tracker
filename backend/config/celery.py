"""Celery asynchronous task queue configuration.

Initialises the Celery application for the finance tracker, configuring
it to load settings from Django with the CELERY namespace and auto-discover
task modules in all installed apps.
"""
from __future__ import absolute_import, unicode_literals
import os
from celery import Celery

# Point Celery to the Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

# Create the Celery application instance
app = Celery('finance_tracker')

# Load Celery configuration from Django settings, using the CELERY_ prefix
app.config_from_object('django.conf:settings', namespace='CELERY')

# Automatically discover tasks.py in each installed app
app.autodiscover_tasks()


@app.task(bind=True)
def debug_task(self):
    """Debug task to verify Celery is working correctly.

    Prints the task request context (useful for testing connectivity
    between the Django app and the Celery worker).
    """
    print(f'Request: {self.request!r}')
