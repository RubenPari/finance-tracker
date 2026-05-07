"""Django application configuration for the suggestions app."""

from django.apps import AppConfig


class SuggestionsConfig(AppConfig):
    """Configuration class for the suggestions Django application.

    Attributes:
        default_auto_field: Specifies the auto-created primary key field type.
        name: Python path to the application package.
        label: Short name used to disambiguate this app within the project.
    """

    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.suggestions'
    label = 'suggestions'
