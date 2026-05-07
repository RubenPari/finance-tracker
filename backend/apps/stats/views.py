"""Statistics and analytics API endpoints for the finance tracker.

This module provides REST API views that compute various financial statistics
from user transactions, including:

    - Financial summaries (total income, expenses, net balance)
    - Category-based expense breakdowns
    - Monthly income and expense trends over a configurable time window
    - Top merchant/description rankings by spending
    - Historical balance over time
    - Period-over-period category spending comparisons

All views inherit from Django REST Framework's APIView and return JSON responses.
Amounts are stored as negative for expenses and positive for income.
"""

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.db.models import Sum, Count, Q
from datetime import datetime, timedelta, date
from dateutil.relativedelta import relativedelta

from apps.transactions.models import Transaction


def get_date_range(request):
    """Calculate the start and end dates for a statistics query based on request parameters.

    Determines the date range to filter transactions by. Supports both explicit
    date ranges (via query parameters) and predefined periods (month, quarter, year).

    Args:
        request: The HTTP request object containing query parameters.
            - period (str): Predefined period to use. One of 'month' (default), 'quarter', or 'year'.
            - date_from (str): Custom start date in 'YYYY-MM-DD' format.
            - date_to (str): Custom end date in 'YYYY-MM-DD' format.

    Returns:
        tuple: A tuple of (date_from, date_to, prev_months) where:
            - date_from (datetime): Start of the query period (inclusive).
            - date_to (datetime): End of the query period (exclusive, day after last day).
            - prev_months (int): Number of months in the period, used for comparison calculations.
    """
    now = datetime.now()
    period = request.query_params.get('period', 'month')
    date_from_str = request.query_params.get('date_from')
    date_to_str = request.query_params.get('date_to')

    if date_from_str and date_to_str:
        # Custom date range: parse and include the full end date by adding one day
        date_from = datetime.strptime(date_from_str, '%Y-%m-%d')
        date_to = datetime.strptime(date_to_str, '%Y-%m-%d')
        date_to = date_to + timedelta(days=1)
        prev_months = 1
    elif period == 'year':
        # Full calendar year from January 1st
        date_from = now.replace(month=1, day=1)
        date_to = date_from + relativedelta(years=1)
        prev_months = 12
    elif period == 'quarter':
        # Current quarter: calculate the first month of the quarter (Jan/Apr/Jul/Oct)
        month = ((now.month - 1) // 3) * 3 + 1
        date_from = now.replace(month=month, day=1)
        date_to = date_from + relativedelta(months=3)
        prev_months = 3
    else:
        # Default: current calendar month
        date_from = now.replace(day=1)
        date_to = date_from + relativedelta(months=1)
        prev_months = 1

    return date_from, date_to, prev_months


class SummaryView(APIView):
    """API endpoint providing an overall financial summary for a given period.

    Computes total income, total expenses, net balance (income minus expenses),
    and the number of transactions within the requested date range.

    Query Parameters:
        period (str): 'month' (default), 'quarter', or 'year'.
        date_from (str): Custom start date in 'YYYY-MM-DD' format.
        date_to (str): Custom end date in 'YYYY-MM-DD' format.

    Returns:
        Response: A JSON object containing:
            - total_expenses (float): Absolute sum of expense transactions.
            - total_income (float): Sum of income transactions.
            - net (float): total_income minus total_expenses.
            - transaction_count (int): Total number of transactions in the period.
            - period_from (str): Start date of the period in ISO format.
            - period_to (str): End date of the period in ISO format.
    """

    def get(self, request):
        """Handle GET request to retrieve the financial summary.

        Args:
            request: The HTTP request object.

        Returns:
            Response: JSON response with summary statistics.
        """
        date_from, date_to, _ = get_date_range(request)

        # Filter transactions for the current user within the computed date range
        qs = Transaction.objects.filter(
            user=request.user,
            completed_at__gte=date_from,
            completed_at__lt=date_to,
        )

        # Aggregate: sum of expenses (negative amounts), sum of income (positive amounts), and count
        aggregates = qs.aggregate(
            total_expenses=Sum('amount', filter=Q(amount__lt=0)),
            total_income=Sum('amount', filter=Q(amount__gt=0)),
            count=Count('id'),
        )

        # Convert to positive float for display (expenses are stored as negative)
        total_expense = abs(float(aggregates['total_expenses'] or 0))
        total_income = float(aggregates['total_income'] or 0)

        return Response({
            'total_expenses': total_expense,
            'total_income': total_income,
            'net': total_income - total_expense,
            'transaction_count': aggregates['count'],
            'period_from': date_from.date().isoformat(),
            'period_to': (date_to - timedelta(days=1)).isoformat(),
        })


class ByCategoryView(APIView):
    """API endpoint providing an expense breakdown by category.

    Groups expense transactions (negative amounts) by their associated category
    and computes the total spent and transaction count per category within
    the requested date range.

    Query Parameters:
        period (str): 'month' (default), 'quarter', or 'year'.
        date_from (str): Custom start date in 'YYYY-MM-DD' format.
        date_to (str): Custom end date in 'YYYY-MM-DD' format.

    Returns:
        Response: A JSON array of objects, each containing:
            - category_id (int): The category's primary key.
            - category_name (str): The category's display name.
            - color (str): Hex color code for chart visualization.
            - total (float): Absolute total amount spent in this category.
            - count (int): Number of transactions in this category.
        Results are ordered by total ascending (smallest spending first).
    """

    def get(self, request):
        """Handle GET request to retrieve category-based expense breakdown.

        Args:
            request: The HTTP request object.

        Returns:
            Response: JSON array of category expense objects.
        """
        date_from, date_to, _ = get_date_range(request)

        # Filter only expense transactions (amount < 0) within the date range,
        # group by category and aggregate total amount and transaction count
        data = Transaction.objects.filter(
            user=request.user,
            amount__lt=0,
            completed_at__gte=date_from,
            completed_at__lt=date_to,
        ).values('category__name', 'category__color', 'category__id').annotate(
            total=Sum('amount'),
            count=Count('id'),
        ).order_by('total')

        return Response([{
            'category_id': item['category__id'],
            'category_name': item['category__name'] or 'Senza categoria',
            'color': item['category__color'] or '#6B7280',
            # Convert negative total to positive absolute value
            'total': abs(float(item['total'])),
            'count': item['count'],
        } for item in data])


class MonthlyTrendView(APIView):
    """API endpoint providing monthly income and expense trends.

    Computes income and expenses for each month in a configurable lookback window,
    returning a time series suitable for line or bar chart visualization.

    Query Parameters:
        months (int): Number of months to look back. Defaults to 12.

    Returns:
        Response: A JSON array of monthly objects, each containing:
            - year (int): Calendar year of the month.
            - month (int): Month number (1-12).
            - month_label (str): Human-readable label (e.g., 'Jan 2026').
            - expenses (float): Total expenses for the month (absolute value).
            - income (float): Total income for the month.
    """

    def get(self, request):
        """Handle GET request to retrieve monthly trend data.

        Args:
            request: The HTTP request object.

        Returns:
            Response: JSON array of monthly trend objects ordered chronologically.
        """
        months = int(request.query_params.get('months', 12))

        result = []
        # Start from the first day of the current month
        current = datetime.now().replace(day=1)

        # Iterate backwards to generate data for each month in the window.
        # The loop computes the start of each period relative to the window size
        # so that the earliest month comes first in the result list.
        for i in range(months):
            period_start = current - relativedelta(months=months - 1 - i)
            period_end = period_start + relativedelta(months=1)

            qs = Transaction.objects.filter(
                user=request.user,
                completed_at__gte=period_start,
                completed_at__lt=period_end,
            )

            # Compute expenses (negative amounts) and income (positive amounts) separately
            expenses = qs.filter(amount__lt=0).aggregate(
                total=Sum('amount')
            )['total'] or 0

            income = qs.filter(amount__gt=0).aggregate(
                total=Sum('amount')
            )['total'] or 0

            result.append({
                'year': period_start.year,
                'month': period_start.month,
                'month_label': period_start.strftime('%b %Y'),
                'expenses': abs(float(expenses)),
                'income': float(income),
            })

        return Response(result)


class TopMerchantsView(APIView):
    """API endpoint providing the top spending merchants (by description).

    Groups expense transactions by their description field (representing the
    merchant or payee) and returns the highest-spending entries, ordered by
    total amount spent.

    Query Parameters:
        period (str): 'month' (default), 'quarter', or 'year'.
        date_from (str): Custom start date in 'YYYY-MM-DD' format.
        date_to (str): Custom end date in 'YYYY-MM-DD' format.
        limit (int): Maximum number of merchants to return. Defaults to 5.

    Returns:
        Response: A JSON array of merchant objects, each containing:
            - merchant (str): The transaction description (merchant name).
            - total (float): Total amount spent with this merchant (absolute value).
            - count (int): Number of transactions with this merchant.
    """

    def get(self, request):
        """Handle GET request to retrieve top merchants by spending.

        Args:
            request: The HTTP request object.

        Returns:
            Response: JSON array of top merchant objects, limited by the `limit` parameter.
        """
        date_from, date_to, _ = get_date_range(request)
        limit = int(request.query_params.get('limit', 5))

        # Filter expense transactions within the date range, group by description,
        # and rank by total spending (ascending, so the largest are at the end of order_by)
        data = Transaction.objects.filter(
            user=request.user,
            amount__lt=0,
            completed_at__gte=date_from,
            completed_at__lt=date_to,
        ).values('description').annotate(
            total=Sum('amount'),
            count=Count('id'),
        ).order_by('total')[:limit]

        return Response([{
            'merchant': item['description'],
            'total': abs(float(item['total'])),
            'count': item['count'],
        } for item in data])


class BalanceView(APIView):
    """API endpoint providing historical balance data over time.

    Returns the running balance after each completed transaction, ordered
    chronologically. This data is suitable for plotting a balance history chart.

    The view only includes transactions that have a non-null balance_after value,
    which represents the account balance immediately after that transaction.

    Query Parameters:
        None.

    Returns:
        Response: A JSON array of balance snapshot objects, each containing:
            - date (str): ISO-formatted timestamp of the transaction completion.
            - balance (float): The account balance after the transaction.
    """

    def get(self, request):
        """Handle GET request to retrieve balance history.

        Args:
            request: The HTTP request object.

        Returns:
            Response: JSON array of balance snapshots ordered chronologically.
        """
        # Fetch all transactions with a recorded balance, ordered by completion date
        transactions = Transaction.objects.filter(
            user=request.user,
            balance_after__isnull=False,
        ).order_by('completed_at').values('completed_at', 'balance_after')

        return Response([{
            'date': t['completed_at'].isoformat(),
            'balance': float(t['balance_after']),
        } for t in transactions])


class ComparisonView(APIView):
    """API endpoint providing period-over-period category spending comparison.

    Compares expense totals by category between the current period (as determined
    by get_date_range) and the immediately preceding period of equal length.
    Calculates the percentage change in spending for each category.

    The percentage change calculation handles edge cases:
        - Returns None if the category did not exist in the previous period.
        - Uses a minimum divisor of 1 to avoid division by zero.

    Query Parameters:
        period (str): 'month' (default), 'quarter', or 'year'.
        date_from (str): Custom start date in 'YYYY-MM-DD' format.
        date_to (str): Custom end date in 'YYYY-MM-DD' format.

    Returns:
        Response: A JSON array of category comparison objects, each containing:
            - category (str): Category display name.
            - color (str): Hex color code for chart visualization.
            - current (float): Total expenses in the current period (absolute value).
            - previous (float): Total expenses in the previous period (absolute value).
            - change_pct (float or None): Percentage change from previous to current period,
              rounded to 1 decimal place, or None if previous period had no data.
    """

    def get(self, request):
        """Handle GET request to retrieve category spending comparison data.

        Args:
            request: The HTTP request object.

        Returns:
            Response: JSON array of category comparison objects with change percentages.
        """
        date_from, date_to, prev_months = get_date_range(request)
        # Calculate the previous period as the same duration immediately before the current period
        prev_from = date_from - timedelta(days=prev_months * 30)
        prev_to = date_from

        # Aggregate current period expenses by category (with color for display)
        current = Transaction.objects.filter(
            user=request.user,
            amount__lt=0,
            completed_at__gte=date_from,
            completed_at__lt=date_to,
        ).values('category__name', 'category__color').annotate(
            total=Sum('amount'),
        )

        # Aggregate previous period expenses by category (no color needed for lookup)
        previous = Transaction.objects.filter(
            user=request.user,
            amount__lt=0,
            completed_at__gte=prev_from,
            completed_at__lt=prev_to,
        ).values('category__name').annotate(
            total=Sum('amount'),
        )

        # Build a lookup dictionary from category name to previous period total
        prev_map = {p['category__name']: p['total'] for p in previous}

        return Response([{
            'category': c['category__name'] or 'Senza categoria',
            'color': c['category__color'] or '#6B7280',
            'current': abs(float(c['total'])),
            'previous': abs(float(prev_map.get(c['category__name'], 0))),
            # Calculate percentage change; None if category didn't exist in previous period.
            # Use max(..., 1) as the denominator to prevent division by zero.
            'change_pct': round(
                ((abs(float(c['total'])) - abs(float(prev_map.get(c['category__name'], 0))))
                 / max(abs(float(prev_map.get(c['category__name'], 1))), 1)) * 100, 1
            ) if prev_map.get(c['category__name']) else None,
        } for c in current])
