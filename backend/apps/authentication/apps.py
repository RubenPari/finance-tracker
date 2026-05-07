"""
Application configuration for the authentication module.

Registers the authentication app with Django's application registry,
configuring auto-generated primary key fields and app labeling.
"""

from django.apps import AppConfig


class AuthenticationConfig(AppConfig):
    """Django application configuration for the authentication module.

    Attributes:
        default_auto_field: Specifies the default auto-incrementing primary
            key type for models in this app.
        name: Full Python path to the app package.
        label: Short label used to distinguish this app in Django's registry.
    """

    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.authentication'
    label = 'authentication'
