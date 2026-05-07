"""Database models for the budgets application.

Contains the Budget model which represents a spending limit set by a user
for a specific category within a given month and year. Each budget entry
tracks how much a user is allowed to spend on a particular expense category
during a specific calendar month.
"""

from django.db import models
from django.conf import settings


class Budget(models.Model):
    """A monthly spending budget for a specific category.

    Represents a spending limit that a user sets for a particular category
    during a specific month and year. Used to track whether the user is
    staying within their planned spending for that category.

    Attributes:
        user: ForeignKey to the user who owns this budget. Deleted if the
            user is removed (CASCADE).
        category: ForeignKey to the expense category this budget applies to.
            Deleted if the category is removed (CASCADE).
        year: The calendar year for this budget (e.g., 2026).
        month: The calendar month for this budget (1-12).
        amount_limit: The maximum spending amount allowed for this category
            in this month, stored as a decimal with up to 10 digits total
            and 2 decimal places (e.g., 99999999.99).

    Meta:
        db_table: Custom table name 'budgets' in the database.
        unique_together: Ensures a user can only have one budget per
            category per month/year combination.
        ordering: Orders budgets by most recent year and month first.
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='budgets',
    )
    category = models.ForeignKey(
        'categories.Category',
        on_delete=models.CASCADE,
        related_name='budgets',
    )
    year = models.IntegerField()
    month = models.IntegerField()
    amount_limit = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        """Meta options for the Budget model.

        Configures the database table name, uniqueness constraints,
        and default ordering for querysets.
        """

        db_table = 'budgets'
        unique_together = [('user', 'category', 'year', 'month')]
        ordering = ['-year', '-month']

    def __str__(self):
        """Return a human-readable string representation of the budget.

        Returns:
            str: Formatted string showing the category name, month/year,
                and budget amount (e.g., 'Groceries 03/2026: 500.00€').
        """
        return f'{self.category.name} {self.month:02d}/{self.year}: {self.amount_limit}€'
