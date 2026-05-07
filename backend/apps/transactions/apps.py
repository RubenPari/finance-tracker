"""App configuration for the transactions Django application.

Registers the ``TransactionsConfig`` class so Django can discover the app
and apply its models, signals, and other initialization logic.
"""

from django.apps import AppConfig


class TransactionsConfig(AppConfig):
    """Configuration for the transactions application.

    Specifies the app's Python path, label, and primary key field type.
    """

    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.transactions'
    label = 'transactions'
