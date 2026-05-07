"""Serializers for the budgets application.

Provides serialization and deserialization of Budget model instances,
including computed fields for spending progress tracking such as
current spent amounts and budget utilization percentages.
"""

from rest_framework import serializers
from .models import Budget


class BudgetSerializer(serializers.ModelSerializer):
    """Serializer for Budget model with progress calculation fields.

    Extends the base Budget model serializer to include computed fields
    that show how much the user has spent in the budgeted category for
    the specified month and what percentage of the budget has been used.

    Fields:
        category_name: Read-only name of the associated category.
        category_color: Read-only color identifier for the category.
        current_spent: Computed absolute value of expenses for the
            budgeted category and month. Cached on the model instance
            if pre-annotated by the view to avoid redundant queries.
        percentage: Computed utilization percentage (current_spent /
            amount_limit * 100), rounded to one decimal place.
    """

    category_name = serializers.CharField(source='category.name', read_only=True)
    category_color = serializers.CharField(source='category.color', read_only=True)
    current_spent = serializers.SerializerMethodField()
    percentage = serializers.SerializerMethodField()

    class Meta:
        """Meta options for BudgetSerializer.

        Specifies the model to serialize and which fields to expose,
        including both model fields and computed fields.
        """

        model = Budget
        fields = (
            'id', 'category', 'category_name', 'category_color',
            'year', 'month', 'amount_limit', 'current_spent', 'percentage',
        )
        read_only_fields = ('id',)

    def get_current_spent(self, obj):
        """Calculate or retrieve the cached spent amount for this budget.

        First checks if the spent amount has been pre-calculated and cached
        on the model instance (via the view's queryset annotation). If not,
        performs a database query to sum all negative transactions (expenses)
        for the same user and category within the budget's month.

        Args:
            obj: The Budget instance to calculate spent amount for.

        Returns:
            float: The absolute value of total expenses for the budget's
                category and month. Returns 0.0 if no expenses exist.
        """
        # Use cached value if pre-annotated by the view to avoid N+1 queries
        if hasattr(obj, '_current_spent'):
            return obj._current_spent

        # Fallback: calculate spent amount when serializer is used standalone
        from django.db.models import Sum
        from apps.transactions.models import Transaction
        import datetime

        # Determine the month's date range for filtering transactions
        start_date = datetime.date(obj.year, obj.month, 1)
        end_date = datetime.date(obj.year, obj.month + 1, 1) if obj.month < 12 else datetime.date(obj.year + 1, 1, 1)

        # Sum all negative amounts (expenses) for this user/category in the month
        spent = Transaction.objects.filter(
            user=obj.user,
            category=obj.category,
            amount__lt=0,
            completed_at__gte=start_date,
            completed_at__lt=end_date,
        ).aggregate(total=Sum('amount'))['total']

        # Cache the result on the instance to avoid recalculation
        obj._current_spent = abs(float(spent or 0))
        return obj._current_spent

    def get_percentage(self, obj):
        """Calculate the budget utilization percentage.

        Computes what percentage of the budget limit has been spent.
        Uses the current_spent value (either cached or freshly calculated).

        Args:
            obj: The Budget instance to calculate percentage for.

        Returns:
            float: The percentage of budget used, rounded to 1 decimal
                place. Returns 0 if the budget limit is zero to avoid
                division by zero.
        """
        current = self.get_current_spent(obj)
        limit = float(obj.amount_limit)
        # Prevent division by zero when budget limit is not set
        if limit == 0:
            return 0
        return round((current / limit) * 100, 1)
