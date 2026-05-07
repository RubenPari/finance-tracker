"""Django application configuration for the budgets app.

Defines the app configuration class that registers the budgets application
with Django's app registry and configures app-level settings.
"""

from django.apps import AppConfig


class BudgetsConfig(AppConfig):
    """Configuration class for the budgets application.

    Attributes:
        default_auto_field: Specifies the default auto field type for models
            in this app. Uses BigAutoField for 64-bit integer primary keys.
        name: The full Python path to the app package.
        label: A short name used to differentiate this app from others
            that might have conflicting names.
    """

    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.budgets'
    label = 'budgets'
