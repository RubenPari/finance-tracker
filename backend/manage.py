#!/usr/bin/env python
"""Django's command-line utility for administrative tasks.

This is the entry point for all Django management commands
(e.g., runserver, migrate, createsuperuser). It configures the
Django settings module and delegates to Django's management framework.
"""
import os
import sys


def main():
    """Run administrative tasks.

    Sets the DJANGO_SETTINGS_MODULE environment variable to point to
    config.settings, then imports and executes the requested management
    command via execute_from_command_line().
    """
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    main()
