"""
Django application configuration for the categories app.

Registers the categories application with Django, specifying the default
auto field type and the application's Python path.
"""

from django.apps import AppConfig


class CategoriesConfig(AppConfig):
    """Configuration class for the categories Django application.

    Sets the default primary key field type to BigAutoField for all
    models in this app and identifies the application namespace.

    Attributes:
        default_auto_field: Default primary key field type for models.
        name: Full Python path to the application package.
        label: Short label used to distinguish this app in Django internals.
    """
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.categories'
    label = 'categories'
