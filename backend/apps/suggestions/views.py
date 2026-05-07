"""Transaction suggestion endpoints for the finance tracker API.

This module provides REST API views that analyze a user's transaction history
and return personalized spending insights. It attempts to generate suggestions
via an AI gateway first, falling back to a statistical/legacy algorithm when
the AI service is unavailable or returns invalid data.
"""

from rest_framework.response import Response
from rest_framework.views import APIView
from django.db.models import Sum, Count, Q, Avg, StdDev
from django.db.models.functions import TruncMonth, TruncDay
from django.utils import timezone
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from calendar import month_name

from apps.transactions.models import Transaction
from .ai_service import generate_suggestions as generate_ai_suggestions


class SuggestionsView(APIView):
    """API view that returns personalized finance suggestions for the authenticated user.

    The view first attempts to generate AI-powered suggestions. If the AI service
    is unavailable or returns None, it falls back to the legacy statistical analysis.
    """

    def get(self, request):
        """Handle GET requests to retrieve suggestions.

        Args:
            request: The HTTP request object containing the authenticated user.

        Returns:
            Response: A DRF Response containing a list of suggestion dictionaries.
        """
        # Build aggregated spending context from the user's transaction history
        # and pass it to the AI suggestion generator
        suggestions = generate_ai_suggestions(
            request.user,
            _build_ai_context(request.user),
        )

        # Fall back to rule-based statistical analysis when AI is unavailable
        if suggestions is None:
            suggestions = _generate_legacy_suggestions(request.user)

        return Response(suggestions)


def _build_ai_context(user):
    """Build an anonymized, aggregated spending context dictionary for the AI gateway.

    Collects the user's transaction data over the last 6 months and computes
    several statistical summaries: monthly spending trends, top spending categories,
    month-over-month category changes, detected recurring subscriptions, and
    anomalous outlier transactions.

    Args:
        user: The Django user whose transaction data to aggregate.

    Returns:
        dict: A context dictionary containing:
            - total_spent_6m (float): Total expenditure over the last 6 months.
            - transactions_count_6m (int): Number of transactions in the period.
            - monthly_trends (list): Monthly aggregated spending with labels.
            - top_categories (list): Top 10 spending categories by total amount.
            - monthly_changes (list): Top 5 categories with largest month-over-month
              percentage change.
            - subscriptions (list): Up to 5 detected recurring subscription patterns.
            - outliers (list): Up to 3 recent transactions flagged as statistical
              outliers (amount > mean + 2*std deviation and > 2*mean).
    """
    now = timezone.now()
    six_months_ago = now - relativedelta(months=6)
    # Compute the first day of the current month at midnight for month boundary queries
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    prev_month_start = month_start - relativedelta(months=1)

    # Compute monthly spending trends for the last 6 months
    # Group transactions by month, summing amounts and counting transactions
    # Only expenses (amount < 0) are included
    monthly = list(
        Transaction.objects.filter(
            user=user,
            amount__lt=0,
            completed_at__gte=six_months_ago,
        ).annotate(
            month=TruncMonth('completed_at')
        ).values('month').annotate(
            total=Sum('amount'),
            count=Count('id'),
        ).order_by('month')
    )

    # Transform raw monthly aggregates into human-readable trend entries
    monthly_trends = []
    for m in monthly:
        monthly_trends.append({
            'month_label': month_name[m['month'].month] if m['month'] else 'Unknown',
            'total': round(abs(float(m['total'])), 2),
            'count': m['count'],
        })

    # Identify top spending categories over the last 6 months
    # Categories are ordered by total spent (ascending, since amounts are negative),
    # so the first results are the highest spenders
    categories = list(
        Transaction.objects.filter(
            user=user,
            amount__lt=0,
            completed_at__gte=six_months_ago,
        ).values('category__name', 'category__color').annotate(
            total=Sum('amount'),
            count=Count('id'),
        ).order_by('total')[:10]
    )
    top_categories = []
    for c in categories:
        top_categories.append({
            'name': c['category__name'] or 'Uncategorized',
            'total': round(abs(float(c['total'])), 2),
            'count': c['count'],
        })

    # Compute month-over-month spending changes per category
    # Compare current month totals against the previous month
    current_totals = {}
    for c in Transaction.objects.filter(
        user=user, amount__lt=0,
        completed_at__gte=month_start,
    ).values('category__name').annotate(total=Sum('amount')):
        current_totals[c['category__name'] or 'Uncategorized'] = abs(float(c['total']))

    prev_totals = {}
    for c in Transaction.objects.filter(
        user=user, amount__lt=0,
        completed_at__gte=prev_month_start,
        completed_at__lt=month_start,
    ).values('category__name').annotate(total=Sum('amount')):
        prev_totals[c['category__name'] or 'Uncategorized'] = abs(float(c['total']))

    # Calculate percentage change for each category between the two months
    changes = []
    for name, cur in current_totals.items():
        prev = prev_totals.get(name, 0)
        if prev > 0:
            # Standard percentage change calculation
            pct = round(((cur - prev) / prev) * 100, 1)
        else:
            # When there was no spending in the previous month,
            # treat any new spending as 100% change (or 0% if no spending now either)
            pct = 100.0 if cur > 0 else 0.0
        changes.append({
            'category': name,
            'current': round(cur, 2),
            'previous': round(prev, 2),
            'change_pct': pct,
        })
    # Sort by absolute percentage change descending to surface the most significant shifts
    changes.sort(key=lambda x: abs(x['change_pct']), reverse=True)

    # Detect potential recurring subscriptions by grouping transactions by description
    # A subscription is identified when the same description appears 3+ times
    # in the last 3 months with a consistent amount
    sub_groups = list(
        Transaction.objects.filter(
            user=user,
            amount__lt=0,
            completed_at__gte=now - relativedelta(months=3),
        ).values('description').annotate(
            count=Count('id'), avg_amount=Avg('amount')
        ).filter(count__gte=3).order_by('-count')[:5]
    )
    subscriptions = []
    for s in sub_groups:
        subscriptions.append({
            'merchant': s['description'],
            'occurrences': s['count'],
            'estimated_monthly': round(abs(float(s['avg_amount'])), 2),
        })

    # Identify statistical outlier transactions using z-score methodology
    # First, compute the mean and standard deviation of spending per category
    # over the last 6 months
    stats = {}
    for item in Transaction.objects.filter(
        user=user, amount__lt=0,
        completed_at__gte=now - relativedelta(months=6),
    ).values('category__name').annotate(avg=Avg('amount'), std=StdDev('amount')):
        # Only consider categories with valid standard deviation (> 0)
        if item['std'] and item['std'] > 0:
            stats[item['category__name'] or 'Uncategorized'] = {
                'avg': abs(float(item['avg'])),
                'std': float(item['std']),
            }

    # Scan the last month's transactions against the category statistics
    # A transaction is an outlier if its amount exceeds both:
    #   1. mean + 2 * standard deviation (statistical threshold)
    #   2. 2 * mean (absolute magnitude threshold to catch small-std categories)
    recent_outliers = []
    months1_ago = now - relativedelta(months=1)
    for tx in Transaction.objects.filter(
        user=user, amount__lt=0,
        completed_at__gte=months1_ago,
    ).select_related('category').order_by('-completed_at')[:20]:
        name = tx.category.name if tx.category else 'Uncategorized'
        if name in stats:
            s = stats[name]
            amt = abs(float(tx.amount))
            if amt > s['avg'] + 2 * s['std'] and amt > s['avg'] * 2:
                recent_outliers.append({
                    'category': name,
                    'amount': round(amt, 2),
                    'average': round(s['avg'], 2),
                })

    return {
        'total_spent_6m': round(sum(m['total'] for m in monthly_trends), 2),
        'transactions_count_6m': sum(m['count'] for m in monthly_trends),
        'monthly_trends': monthly_trends,
        'top_categories': top_categories,
        'monthly_changes': changes[:5],
        'subscriptions': subscriptions,
        'outliers': recent_outliers[:3],
    }


def _generate_legacy_suggestions(user):
    """Generate fallback suggestions using rule-based statistical analysis.

    This function serves as a fallback when the AI gateway is unavailable.
    It combines the results of multiple detection algorithms into a single
    list of suggestions: biggest spending increase, recurring subscriptions,
    spending peaks by day of week, and outlier transactions.

    Args:
        user: The Django user to analyze.

    Returns:
        list: A list of suggestion dictionaries, each containing at minimum
            'type', 'title', and 'message' keys.
    """
    suggestions = []

    # Detect the category with the largest month-over-month spending increase
    biggest_increase = _detect_biggest_increase(user)
    if biggest_increase:
        suggestions.append(biggest_increase)

    # Detect potential recurring subscriptions from transaction patterns
    subscriptions = _detect_subscriptions(user)
    for sub in subscriptions:
        suggestions.append(sub)

    # Identify the day of week with the highest aggregate spending
    spending_peaks = _detect_spending_peaks(user)
    if spending_peaks:
        suggestions.append(spending_peaks)

    # Find individual transactions that are statistical anomalies
    outliers = _detect_outliers(user)
    for outlier in outliers:
        suggestions.append(outlier)

    return suggestions


# ===== Legacy detection functions (unchanged) =====


def _detect_biggest_increase(user):
    """Find the spending category with the largest month-over-month increase.

    Compares current month spending to the previous month for each category
    and returns the one with the highest percentage increase.

    Args:
        user: The Django user to analyze.

    Returns:
        dict or None: A suggestion dictionary for the category with the biggest
            increase, or None if there is no spending data.
    """
    now = datetime.now()
    current_start = now.replace(day=1)
    prev_start = current_start - relativedelta(months=1)
    prev_end = current_start

    # Get current month spending totals per category
    current_totals = Transaction.objects.filter(
        user=user, amount__lt=0,
        completed_at__gte=current_start,
        completed_at__lt=current_start + relativedelta(months=1),
    ).values('category__name', 'category__color').annotate(
        total=Sum('amount'),
    )

    # No spending this month means no increase to report
    if not current_totals:
        return None

    # Build a lookup map of previous month's totals by category name
    prev_totals_map = {}
    for item in Transaction.objects.filter(
        user=user, amount__lt=0,
        completed_at__gte=prev_start,
        completed_at__lt=prev_end,
    ).values('category__name').annotate(
        total=Sum('amount'),
    ):
        prev_totals_map[item['category__name']] = item['total']

    # Iterate through current month categories to find the biggest percentage increase
    biggest = None
    biggest_pct = 0

    for c in current_totals:
        name = c['category__name'] or 'Uncategorized'
        cur = abs(float(c['total']))
        prev = abs(float(prev_totals_map.get(name, 0)))
        # Only consider categories that existed last month and actually increased
        if prev > 0 and cur > prev:
            pct = ((cur - prev) / prev) * 100
            if pct > biggest_pct:
                biggest_pct = pct
                biggest = {
                    'type': 'biggest_increase',
                    'title': f'Increase in {name}',
                    'message': (
                        f'Spending in {name} increased by {round(pct, 1)}% '
                        f'compared to last month (from {prev:.2f}€ to {cur:.2f}€).'
                    ),
                    'category': name,
                    'color': c.get('category__color', '#6B7280'),
                    'current_amount': cur,
                    'previous_amount': prev,
                    'change_pct': round(pct, 1),
                }

    return biggest


def _detect_subscriptions(user):
    """Detect potential recurring subscriptions from transaction patterns.

    Identifies transactions with the same description and amount that occur
    at least 3 times in the last 3 months, suggesting a recurring payment
    pattern such as a monthly subscription.

    Args:
        user: The Django user to analyze.

    Returns:
        list: A list of suggestion dictionaries for detected subscription patterns,
            ordered by occurrence count (descending).
    """
    three_months_ago = datetime.now() - relativedelta(months=3)

    # Group transactions by both description and amount to find exact recurring charges
    # Filter to groups with 3 or more occurrences, suggesting a monthly pattern
    groups = Transaction.objects.filter(
        user=user,
        amount__lt=0,
        completed_at__gte=three_months_ago,
    ).values('description', 'amount').annotate(
        count=Count('id'),
    ).filter(count__gte=3).order_by('-count')

    suggestions = []
    # Return at most 5 detected subscription patterns
    for g in groups[:5]:
        amount = abs(float(g['amount']))
        suggestions.append({
            'type': 'subscription',
            'title': 'Possible subscription',
            'message': (
                f'"{g["description"]}" appears {g["count"]} times in the last 3 months '
                f'for a total of {amount * g["count"]:.2f}€. '
                f'This may be a recurring subscription.'
            ),
            'merchant': g['description'],
            'amount': amount,
            'occurrences': g['count'],
        })

    return suggestions


def _detect_spending_peaks(user):
    """Identify the day of the week with the highest aggregate spending.

    Analyzes 6 months of transaction data to determine which day of the week
    the user tends to spend the most money on, providing a behavioral spending
    insight.

    Args:
        user: The Django user to analyze.

    Returns:
        dict or None: A suggestion dictionary identifying the peak spending day,
            or None if there is no transaction data.
    """
    transactions = Transaction.objects.filter(
        user=user,
        amount__lt=0,
        completed_at__gte=datetime.now() - relativedelta(months=6),
    ).annotate(day_of_week=TruncDay('completed_at')).values('day_of_week').annotate(
        total=Sum('amount'),
        count=Count('id'),
    ).order_by('total')

    if not transactions:
        return None

    # Results are ordered by total ascending (negative amounts),
    # so the first entry has the most spending (most negative total)
    worst = transactions[0]
    day_name = worst['day_of_week'].strftime('%A')

    # Map English day names to Italian for display
    days_it = {
        'Monday': 'Lunedì', 'Tuesday': 'Martedì', 'Wednesday': 'Mercoledì',
        'Thursday': 'Giovedì', 'Friday': 'Venerdì', 'Saturday': 'Sabato', 'Sunday': 'Domenica',
    }

    return {
        'type': 'spending_peaks',
        'title': 'Spending peak',
        'message': (
            f'{days_it.get(day_name, day_name)} is the day you spend the most: '
            f'{abs(float(worst["total"])):.2f}€ across {worst["count"]} transactions.'
        ),
        'day': days_it.get(day_name, day_name),
        'total': abs(float(worst['total'])),
        'count': worst['count'],
    }


def _detect_outliers(user):
    """Detect individual transactions that are statistical anomalies.

    Identifies transactions where the amount exceeds both:
    - The category mean plus 2 standard deviations (statistical threshold)
    - Twice the category mean (absolute magnitude threshold)

    This dual-threshold approach ensures we catch both genuinely unusual
    spending and avoid flagging small transactions in low-variance categories.

    Args:
        user: The Django user to analyze.

    Returns:
        list: A list of up to 5 suggestion dictionaries for anomalous transactions,
            ordered by recency.
    """
    now = datetime.now()
    month_start = now.replace(day=1)

    # Compute per-category statistics over the last 6 months
    # These establish the baseline "normal" spending for each category
    category_avg = Transaction.objects.filter(
        user=user,
        amount__lt=0,
        completed_at__gte=now - relativedelta(months=6),
    ).values('category__name', 'category__color').annotate(
        avg=Avg('amount'),
        std=StdDev('amount'),
    )

    # Build a lookup dictionary of category statistics
    stats = {}
    for item in category_avg:
        name = item['category__name'] or 'Uncategorized'
        # Only include categories with a valid standard deviation
        if item['std'] and item['std'] > 0:
            stats[name] = {
                'avg': abs(float(item['avg'])),
                'std': float(item['std']),
                'color': item.get('category__color', '#6B7280'),
            }

    # Scan recent transactions (last month) against the category baselines
    outliers = []
    recent = Transaction.objects.filter(
        user=user,
        amount__lt=0,
        completed_at__gte=now - relativedelta(months=1),
    ).select_related('category')

    for tx in recent:
        name = tx.category.name if tx.category else 'Uncategorized'
        if name in stats:
            s = stats[name]
            tx_amount = abs(float(tx.amount))
            # A transaction is flagged as an outlier when it exceeds both thresholds:
            # 1. More than 2 standard deviations above the mean (statistical anomaly)
            # 2. More than double the average transaction (absolute magnitude)
            if tx_amount > s['avg'] + 2 * s['std'] and tx_amount > s['avg'] * 2:
                outliers.append({
                    'type': 'outlier',
                    'title': 'Anomalous spending',
                    'message': (
                        f'Transaction of {tx_amount:.2f}€ at "{tx.description}" '
                        f'in {name}. The average for this category is {s["avg"]:.2f}€.'
                    ),
                    'transaction_id': tx.id,
                    'description': tx.description,
                    'amount': tx_amount,
                    'category': name,
                    'color': s['color'],
                    'average': s['avg'],
                })

    # Return at most 5 outliers to avoid overwhelming the user
    return outliers[:5]
