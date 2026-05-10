"""
Django REST Framework views for the categories application.

Provides CRUD API endpoints for managing categories and categorization rules,
as well as an AI-powered endpoint that automatically assigns categories to
uncategorized transactions using an external AI gateway service.
"""

from django.db import models
from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.generics import (
    ListAPIView,
    CreateAPIView,
    UpdateAPIView,
    DestroyAPIView,
)

from .models import Category, CategoryRule
from .serializers import CategorySerializer, CategoryRuleSerializer
from apps.transactions.models import Transaction
from .ai_categorization import batch_categorize


# Built-in system categories provided to all users as defaults.
# Each entry defines the name, UI color (hex), and icon identifier.
SYSTEM_CATEGORIES = [
    {'name': 'Alimentari', 'color': '#10B981', 'icon': 'shopping-cart'},
    {'name': 'Trasporti', 'color': '#3B82F6', 'icon': 'car'},
    {'name': 'Ristoranti', 'color': '#F59E0B', 'icon': 'utensils'},
    {'name': 'Intrattenimento', 'color': '#8B5CF6', 'icon': 'film'},
    {'name': 'Salute', 'color': '#EF4444', 'icon': 'heart'},
    {'name': 'Shopping', 'color': '#EC4899', 'icon': 'shopping-bag'},
    {'name': 'Abbonamenti', 'color': '#6366F1', 'icon': 'repeat'},
    {'name': 'Investimenti', 'color': '#F97316', 'icon': 'trending-up'},
    {'name': 'Stipendio', 'color': '#14B8A6', 'icon': 'briefcase'},
    {'name': 'Trasferimenti', 'color': '#06B6D4', 'icon': 'arrow-right-left'},
    {'name': 'Prelievi ATM', 'color': '#78716C', 'icon': 'wallet'},
    {'name': 'Cambio Valuta', 'color': '#A3E635', 'icon': 'currency'},
    {'name': 'Altro', 'color': '#6B7280', 'icon': 'more-horizontal'},
]


def _parse_limit(request, default: int = 100, min_value: int = 1, max_value: int = 500) -> int:
    """Parse and validate the `limit` query parameter."""
    raw = request.query_params.get('limit')
    if raw in (None, ''):
        return default

    try:
        value = int(raw)
    except (TypeError, ValueError):
        raise ValidationError({'limit': 'Parametro non valido: deve essere un intero.'})

    if value < min_value or value > max_value:
        raise ValidationError({'limit': f'Valore non valido: consentito tra {min_value} e {max_value}.'})

    return value


class CategoryListView(ListAPIView):
    """List all categories available to the authenticated user.

    Returns both user-defined categories and system default categories.
    Results are not paginated to support dropdown selectors in the UI.
    """
    serializer_class = CategorySerializer
    pagination_class = None

    def get_queryset(self):
        """Return categories belonging to the user plus all system categories.

        Uses a Q object OR query to combine user-owned and system categories.
        """
        return Category.objects.filter(
            models.Q(user=self.request.user) | models.Q(is_system=True),
        )


class CategoryCreateView(CreateAPIView):
    """Create a new user-defined category.

    Automatically associates the new category with the authenticated user.
    """
    serializer_class = CategorySerializer

    def perform_create(self, serializer):
        """Save the category with the authenticated user as the owner."""
        serializer.save(user=self.request.user)


class CategoryUpdateView(UpdateAPIView):
    """Update an existing user-defined category.

    Only allows updating categories that belong to the authenticated user
    and are not system categories. System categories are read-only.
    """
    serializer_class = CategorySerializer

    def get_queryset(self):
        """Return only user-owned, non-system categories for editing."""
        return Category.objects.filter(user=self.request.user, is_system=False)


class CategoryDeleteView(DestroyAPIView):
    """Delete a user-defined category.

    Before deletion, reassigns all transactions that used this category
    to the system fallback category ('Altro') to maintain referential
    integrity. Only user-owned, non-system categories can be deleted.
    """

    def get_queryset(self):
        """Return only user-owned, non-system categories eligible for deletion."""
        return Category.objects.filter(user=self.request.user, is_system=False)

    def destroy(self, request, *args, **kwargs):
        """Delete the category after reassigning its transactions to the fallback.

        Looks up the 'Altro' system category as the fallback target. If the
        fallback exists, all transactions referencing the deleted category
        are updated to point to it instead.
        """
        instance = self.get_object()
        # Find the system fallback category for orphaned transactions
        fallback = Category.objects.filter(is_system=True, name='Altro').first()
        # Reassign all transactions from the deleted category to the fallback
        Transaction.objects.filter(category=instance).update(category=fallback)
        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)


class CategoryRuleListView(ListAPIView):
    """List all categorization rules for the authenticated user.

    Returns rules with their associated category data prefetched to
    avoid N+1 query issues.
    """
    serializer_class = CategoryRuleSerializer

    def get_queryset(self):
        """Return user's rules with related category data eagerly loaded."""
        return CategoryRule.objects.filter(user=self.request.user).select_related('category')


class CategoryRuleCreateView(CreateAPIView):
    """Create a new keyword-based categorization rule for the user."""
    serializer_class = CategoryRuleSerializer

    def perform_create(self, serializer):
        """Save the rule with the authenticated user as the owner."""
        serializer.save(user=self.request.user)


class CategoryRuleDeleteView(DestroyAPIView):
    """Delete a user-defined categorization rule."""

    def get_queryset(self):
        """Return only the user's own rules for deletion."""
        return CategoryRule.objects.filter(user=self.request.user)


class AICategorizeView(APIView):
    """AI-powered bulk transaction categorization endpoint.

    POST /api/categories/ai-categorize/

    Fetches uncategorized transactions for the authenticated user,
    extracts unique descriptions, and sends them to the AI categorization
    service. The AI returns category assignments which are then applied
    to the transactions.

    Query parameters:
        limit: Maximum number of transactions to process (default: 100).

    Returns:
        categorized_count: Number of successfully categorized transactions.
        total_uncategorized: Total number of transactions processed.
        assignments: List of transaction-to-category assignments made.
    """

    def post(self, request, *args, **kwargs):
        """Process uncategorized transactions using AI categorization.

        Args:
            request: The HTTP request object containing optional 'limit' query param.

        Returns:
            Response with categorization results or a message if no
            uncategorized transactions exist.
        """
        # Parse the limit parameter to cap the number of transactions processed
        limit = _parse_limit(request)

        # Fetch the most recent uncategorized transactions up to the limit
        uncategorized = list(
            Transaction.objects.filter(
                user=request.user,
                category__isnull=True,
            ).order_by('-completed_at')[:limit]
        )

        if not uncategorized:
            return Response({
                'categorized_count': 0,
                'message': 'Nessuna transazione da categorizzare.',
            })

        # Extract unique descriptions to minimize AI API calls
        unique_descs = list({tx.description for tx in uncategorized})

        # Send unique descriptions to the AI categorization service
        mapping = batch_categorize(request.user, unique_descs)

        # Build a lookup from category name string to Category model instance
        cat_name_to_obj = {}
        for cat in Category.objects.filter(
            models.Q(user=request.user) | models.Q(is_system=True)
        ):
            cat_name_to_obj[cat.name] = cat

        # Apply AI-assigned categories to each transaction
        categorized_count = 0
        assignments = []
        for tx in uncategorized:
            cat_name = mapping.get(tx.description)
            # Only assign if AI returned a valid category that exists for this user
            if cat_name and cat_name in cat_name_to_obj:
                tx.category = cat_name_to_obj[cat_name]
                tx.save(update_fields=['category'])
                categorized_count += 1
                assignments.append({
                    'transaction_id': tx.id,
                    'description': tx.description,
                    'category': cat_name,
                })

        return Response({
            'categorized_count': categorized_count,
            'total_uncategorized': len(uncategorized),
            'assignments': assignments,
        })
