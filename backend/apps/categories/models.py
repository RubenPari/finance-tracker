"""
Django models for the categories application.

Defines the Category model for grouping finance transactions and the
CategoryRule model for keyword-based automatic categorization rules.
Categories can be system-provided defaults or user-defined custom ones.
"""

from django.db import models
from django.conf import settings


class Category(models.Model):
    """Represents a spending or income category for transactions.

    Categories can be system-defined (shared defaults like 'Alimentari'
    or 'Trasporti') or user-created custom categories. System categories
    cannot be modified or deleted by users.

    Attributes:
        user: ForeignKey to the user who owns this category. Null for system categories.
        name: Human-readable name of the category (max 100 characters).
        color: Hex color code for UI display (7 characters, default '#6B7280').
        icon: Icon identifier for UI display (max 50 characters, default 'category').
        is_system: Boolean flag indicating if this is a built-in system category.

    Meta:
        db_table: Custom database table name 'categories'.
        unique_together: Ensures each user cannot have duplicate category names.
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='categories',
    )
    name = models.CharField(max_length=100)
    color = models.CharField(max_length=7, default='#6B7280')
    icon = models.CharField(max_length=50, default='category')
    is_system = models.BooleanField(default=False)

    class Meta:
        db_table = 'categories'
        unique_together = [('user', 'name')]

    def __str__(self):
        """Return the human-readable name of the category."""
        return self.name


class CategoryRule(models.Model):
    """Represents a keyword-based rule for automatic transaction categorization.

    Rules are user-defined mappings from keywords to categories. When a
    transaction description contains the keyword, it is automatically
    assigned to the associated category. Rules are evaluated by priority
    (highest first), then by creation date (oldest first).

    Attributes:
        user: ForeignKey to the user who owns this rule.
        keyword: The text pattern to match against transaction descriptions.
        category: ForeignKey to the Category assigned when the keyword matches.
        priority: Integer priority level for rule evaluation order (higher = first).
        created_at: Timestamp of when the rule was created.

    Meta:
        db_table: Custom database table name 'category_rules'.
        ordering: Default ordering by descending priority, then ascending created_at.
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='category_rules',
    )
    keyword = models.CharField(max_length=255)
    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        related_name='rules',
    )
    priority = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'category_rules'
        ordering = ['-priority', 'created_at']

    def __str__(self):
        """Return a human-readable representation of the rule mapping."""
        return f'"{self.keyword}" → {self.category.name}'
