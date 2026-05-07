"""API views for budget management.

Provides REST API endpoints for creating, reading, updating, and deleting
budget entries. The list endpoint includes calculated spending progress
by aggregating transactions for each budgeted category within the
specified month.
"""

from rest_framework import status
from rest_framework.response import Response
from rest_framework.generics import (
    ListAPIView,
    CreateAPIView,
    UpdateAPIView,
    DestroyAPIView,
)
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Sum, Subquery, OuterRef, Q
from django.utils import timezone
from datetime import date

from .models import Budget
from .serializers import BudgetSerializer
from apps.transactions.models import Transaction


class BudgetFilter(DjangoFilterBackend):
    """Custom filter backend for filtering budgets by year and month.

    Extends DjangoFilterBackend to provide query parameter-based filtering
    for budget listing endpoints. Allows clients to filter budgets by
    specific year and/or month values.
    """

    def filter_queryset(self, request, queryset, view):
        """Apply year and month filters from query parameters.

        Args:
            request: The HTTP request object containing query parameters.
            queryset: The base queryset to filter.
            view: The view instance making the request.

        Returns:
            QuerySet: The filtered queryset with year and/or month
                constraints applied if provided in query parameters.
        """
        year = request.query_params.get('year')
        month = request.query_params.get('month')
        if year:
            queryset = queryset.filter(year=year)
        if month:
            queryset = queryset.filter(month=month)
        return queryset


class BudgetListView(ListAPIView):
    """List all budgets for the authenticated user with spending progress.

    GET endpoint that returns budgets filtered by year and month query
    parameters (defaults to current month). Each budget includes the
    current spent amount calculated via a subquery annotation to avoid
    N+1 query problems.

    Query Parameters:
        year: Optional. Filter budgets by year (defaults to current year).
        month: Optional. Filter budgets by month 1-12 (defaults to
            current month).

    Permissions:
        Requires authentication. Users can only see their own budgets.

    Response:
        200 OK: List of budget objects with spending progress data.
    """

    serializer_class = BudgetSerializer
    filter_backends = [BudgetFilter]

    def get_queryset(self):
        """Build the queryset with spending annotations for the current user.

        Constructs a queryset that fetches budgets for the authenticated user
        and annotates each budget with the total spent amount for that
        category in the specified month. Uses a subquery to efficiently
        aggregate transactions without N+1 queries.

        Returns:
            QuerySet: Budget queryset annotated with '_spent' field
                containing the sum of negative transaction amounts for
                each budget's category and month.
        """
        now = timezone.now()
        year = int(self.request.query_params.get('year', now.year))
        month = int(self.request.query_params.get('month', now.month))

        # Calculate the start and end dates for the target month
        start_date = date(year, month, 1)
        end_date = date(year + 1, 1, 1) if month == 12 else date(year, month + 1, 1)

        # Subquery to calculate total spent per category for the month
        # Filters for negative amounts (expenses) within the date range
        spent_subquery = Transaction.objects.filter(
            user=OuterRef('user'),
            category=OuterRef('category'),
            amount__lt=0,
            completed_at__gte=start_date,
            completed_at__lt=end_date,
        ).values('category').annotate(
            total=Sum('amount')
        ).values('total')[:1]

        return (
            Budget.objects.filter(user=self.request.user)
            .select_related('category')
            .annotate(_spent=Subquery(spent_subquery))
        )

    def list(self, request, *args, **kwargs):
        """Override list to cache spent amounts on budget instances.

        Processes the queryset to compute and cache the absolute spent
        value on each budget instance before serialization. This allows
        the serializer's get_current_spent method to use the cached value
        instead of performing additional database queries.

        Args:
            request: The HTTP request object.
            *args: Variable length argument list.
            **kwargs: Arbitrary keyword arguments.

        Returns:
            Response: Serialized budget data with spending progress.
        """
        queryset = self.get_queryset()
        for budget in queryset:
            # Cache absolute spent value on instance for serializer access
            budget._current_spent = abs(float(budget._spent or 0))
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class BudgetCreateView(CreateAPIView):
    """Create a new budget for the authenticated user.

    POST endpoint that creates a new budget entry. The user is automatically
    set to the authenticated user from the request, preventing users from
    creating budgets for other users.

    Request Body:
        category: ID of the category to budget for.
        year: Calendar year (integer).
        month: Calendar month 1-12 (integer).
        amount_limit: Maximum spending amount (decimal).

    Permissions:
        Requires authentication.

    Response:
        201 Created: The newly created budget object.
    """

    serializer_class = BudgetSerializer

    def perform_create(self, serializer):
        """Save the new budget with the authenticated user.

        Associates the created budget with the requesting user to ensure
        proper ownership and access control.

        Args:
            serializer: The validated BudgetSerializer instance.
        """
        serializer.save(user=self.request.user)


class BudgetUpdateView(UpdateAPIView):
    """Update an existing budget for the authenticated user.

    PUT/PATCH endpoint that updates a budget identified by its primary key.
    The queryset is scoped to the authenticated user's budgets only,
    preventing unauthorized access to other users' budgets.

    URL Parameters:
        pk: Primary key of the budget to update.

    Request Body:
        Fields to update (category, year, month, amount_limit).

    Permissions:
        Requires authentication. Users can only update their own budgets.

    Response:
        200 OK: The updated budget object.
        404 Not Found: If the budget does not exist or belongs to another user.
    """

    serializer_class = BudgetSerializer

    def get_queryset(self):
        """Return only the authenticated user's budgets.

        Ensures users can only update budgets they own by filtering
        the queryset to the current user.

        Returns:
            QuerySet: Budgets belonging to the authenticated user.
        """
        return Budget.objects.filter(user=self.request.user)


class BudgetDeleteView(DestroyAPIView):
    """Delete an existing budget for the authenticated user.

    DELETE endpoint that removes a budget identified by its primary key.
    The queryset is scoped to the authenticated user's budgets only,
    preventing unauthorized deletion of other users' budgets.

    URL Parameters:
        pk: Primary key of the budget to delete.

    Permissions:
        Requires authentication. Users can only delete their own budgets.

    Response:
        204 No Content: Successfully deleted.
        404 Not Found: If the budget does not exist or belongs to another user.
    """

    def get_queryset(self):
        """Return only the authenticated user's budgets.

        Ensures users can only delete budgets they own by filtering
        the queryset to the current user.

        Returns:
            QuerySet: Budgets belonging to the authenticated user.
        """
        return Budget.objects.filter(user=self.request.user)
