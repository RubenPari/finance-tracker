"""App configuration for the stats Django application."""

from django.apps import AppConfig


class StatsConfig(AppConfig):
    """Django application configuration for the stats module.

    This class configures the stats app's metadata, including the auto-generated
    primary key field type, the Python path to the app, and its unique label
    used in Django internals (e.g., migrations, content types).

    Attributes:
        default_auto_field: Specifies the default auto-incrementing primary key field type.
        name: The Python path to the app (relative to the project root).
        label: A short name used to distinguish this app from others with the same name.
    """

    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.stats'
    label = 'stats'
