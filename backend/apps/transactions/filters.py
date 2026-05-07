"""Filter set for querying transactions with various criteria.

This module defines ``TransactionFilter``, a django-filters FilterSet that enables
API clients to filter transactions by date range, amount range, transaction type,
category, currency, import batch, and income/expense sign.
"""

import django_filters
from .models import Transaction


class TransactionFilter(django_filters.FilterSet):
    """Filter set for narrowing down transaction querysets.

    Provides the following filter parameters:
        date_from: Transactions completed on or after this datetime.
        date_to: Transactions completed on or before this datetime.
        amount_min: Minimum transaction amount.
        amount_max: Maximum transaction amount.
        type: Exact match on transaction type.
        category: Filter by category ID.
        sign: Filter by ``income`` (positive amount) or ``expense`` (negative amount).
        import_batch: Filter by the import batch ID that created the transaction.
    """

    # Date range filters based on completion timestamp
    date_from = django_filters.DateTimeFilter(
        field_name="completed_at", lookup_expr="gte"
    )
    date_to = django_filters.DateTimeFilter(
        field_name="completed_at", lookup_expr="lte"
    )
    # Amount range filters for budget-based queries
    amount_min = django_filters.NumberFilter(field_name="amount", lookup_expr="gte")
    amount_max = django_filters.NumberFilter(field_name="amount", lookup_expr="lte")
    # Categorical and type filters
    type = django_filters.CharFilter(field_name="transaction_type")
    category = django_filters.NumberFilter(field_name="category_id")
    # Custom filter for income vs expense classification
    sign = django_filters.CharFilter(method="filter_sign")
    # Filter by source import batch
    import_batch = django_filters.NumberFilter(field_name="import_batch_id")

    def filter_sign(self, queryset, name, value):
        """Filter transactions by financial direction (income or expense).

        Args:
            queryset: The base transaction queryset.
            name: The filter field name (unused).
            value: Either ``income`` for positive amounts or ``expense`` for negative.

        Returns:
            QuerySet: Filtered queryset based on amount sign.
        """
        if value == "expense":
            return queryset.filter(amount__lt=0)
        if value == "income":
            return queryset.filter(amount__gt=0)
        return queryset

    class Meta:
        model = Transaction
        fields = ["transaction_type", "category", "currency"]
