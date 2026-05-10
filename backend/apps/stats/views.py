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
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView
from django.db.models import Sum, Count, Q
from django.db.models.functions import Lower
from django.utils import timezone
from datetime import datetime, timedelta, date
from dateutil.relativedelta import relativedelta
from statistics import mean, pstdev
import re
import hashlib

from apps.transactions.models import Transaction
from apps.stats.subscriptions_ai import classify_subscription_candidates
from apps.stats.models import SubscriptionOverride


def _parse_int_query_param(request, name: str, default: int, min_value: int, max_value: int) -> int:
    """Parse and validate an integer query parameter with bounds."""
    raw = request.query_params.get(name)
    if raw in (None, ''):
        return default

    try:
        value = int(raw)
    except (TypeError, ValueError):
        raise ValidationError({name: 'Parametro non valido: deve essere un intero.'})

    if value < min_value or value > max_value:
        raise ValidationError({name: f'Valore non valido: consentito tra {min_value} e {max_value}.'})

    return value


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
    now = timezone.now()
    period = request.query_params.get('period', 'month')
    date_from_str = request.query_params.get('date_from')
    date_to_str = request.query_params.get('date_to')

    allowed_periods = {'month', 'quarter', 'year'}
    if period not in allowed_periods:
        raise ValidationError({'period': 'Valore non valido. Usa month, quarter o year.'})

    if bool(date_from_str) != bool(date_to_str):
        raise ValidationError({'date_range': 'Fornisci sia date_from che date_to.'})

    if date_from_str and date_to_str:
        # Custom date range: parse and include the full end date by adding one day
        try:
            date_from = timezone.make_aware(datetime.strptime(date_from_str, '%Y-%m-%d'))
            date_to = timezone.make_aware(datetime.strptime(date_to_str, '%Y-%m-%d'))
        except ValueError:
            raise ValidationError({'date_range': 'Formato data non valido. Usa YYYY-MM-DD.'})

        if date_from > date_to:
            raise ValidationError({'date_range': 'Intervallo non valido: date_from deve precedere date_to.'})

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
        months = _parse_int_query_param(request, 'months', default=12, min_value=1, max_value=60)

        result = []
        # Start from the first day of the current month
        current = timezone.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)

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
        limit = _parse_int_query_param(request, 'limit', default=5, min_value=1, max_value=50)

        # Expenses are stored as negative values, so lower totals mean higher spending.
        # Ordering ascending returns the largest spenders first.
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
        # Calculate the previous period using calendar-aware ranges when possible.
        # For custom ranges, mirror the exact window length.
        if request.query_params.get('date_from') and request.query_params.get('date_to'):
            prev_from = date_from - (date_to - date_from)
        else:
            prev_from = date_from - relativedelta(months=prev_months)
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


# Detection thresholds for recurring subscription inference.
SUBSCRIPTION_LOOKBACK_MONTHS = 12
SUBSCRIPTION_MIN_OCCURRENCES = 2
# Minimum number of intervals (i.e. 2 transactions -> 1 interval) to attempt cadence inference.
SUBSCRIPTION_MIN_INTERVALS = 1
# Tolerance windows (in days) around canonical cadences.
_CADENCE_WINDOWS = [
    ('weekly', 6, 8),
    ('monthly', 25, 35),
    ('quarterly', 85, 95),
    ('yearly', 350, 380),
]


def _classify_cadence(avg_interval_days: float) -> str:
    """Classify the average interval between charges into a cadence label."""
    for label, low, high in _CADENCE_WINDOWS:
        if low <= avg_interval_days <= high:
            return label
    return 'irregular'


_DESC_STOPWORDS = {
    'pagamento',
    'payment',
    'pos',
    'carta',
    'card',
    'transazione',
    'transaction',
    'addebito',
    'debito',
    'revolut',
    'visa',
    'mastercard',
    'mc',
}


def _normalize_description(description: str) -> str:
    """Normalize a transaction description into a stable clustering key."""
    if not description:
        return ''

    s = description.casefold()
    # Keep alphanumerics and a small set of separators, then collapse whitespace.
    s = re.sub(r'[^a-z0-9\s&+\-./]', ' ', s)
    s = re.sub(r'\s+', ' ', s).strip()

    tokens = [t for t in re.split(r'[\s./\-]+', s) if t]
    tokens = [
        t for t in tokens
        if t not in _DESC_STOPWORDS and not t.isdigit() and len(t) > 1
    ]
    if not tokens:
        return s[:64]

    return ' '.join(tokens[:6])[:64]


def _median(values: list[float]) -> float:
    if not values:
        return 0.0
    v = sorted(values)
    n = len(v)
    mid = n // 2
    if n % 2 == 1:
        return float(v[mid])
    return float((v[mid - 1] + v[mid]) / 2.0)


def _mad(values: list[float], med: float | None = None) -> float:
    if not values:
        return 0.0
    m = med if med is not None else _median(values)
    devs = [abs(x - m) for x in values]
    return _median(devs)


def _safe_ratio(num: float, den: float, default: float = 0.0) -> float:
    if den <= 0:
        return default
    return num / den


def _pattern_score(occurrences: int, amount_mad_ratio: float, interval_mad_ratio: float) -> float:
    """Heuristic score 0..1 for recurring-pattern likelihood (pre-AI)."""
    occ = min(max(occurrences, 0), 8)
    occ_score = max(0.0, min(1.0, (occ - 1) / 7.0))  # 2 -> ~0.14, 8 -> 1.0

    amt_score = max(0.0, 1.0 - (amount_mad_ratio / 0.75))  # tolerate variability
    int_score = max(0.0, 1.0 - (interval_mad_ratio / 0.60))

    return round(max(0.0, min(1.0, (0.45 * occ_score + 0.30 * amt_score + 0.25 * int_score))), 3)


def _cluster_key_hash(user_id: int, cluster_key: str) -> str:
    raw = f'{user_id}:{cluster_key}'.encode('utf-8', errors='ignore')
    return hashlib.sha256(raw).hexdigest()


class SubscriptionsView(APIView):
    """API endpoint returning detected recurring subscriptions for the user.

    Groups expense transactions from the last 12 months by normalized description,
    keeps only stable recurring patterns (at least 3 occurrences, amount standard
    deviation <= 25% of the mean), and returns each detected subscription with
    cadence, average amount, next expected charge date, and activity status.
    Also returns a summary with totals and monthly/yearly projections.

    Returns:
        Response: JSON object with 'summary' and 'items' keys.
    """

    def get(self, request):
        """Handle GET request to retrieve detected subscriptions."""
        now = timezone.now()
        lookback_start = now - relativedelta(months=SUBSCRIPTION_LOOKBACK_MONTHS)

        base_qs = (
            Transaction.objects.filter(
                user=request.user,
                amount__lt=0,
                completed_at__gte=lookback_start,
            )
            .select_related('category')
            .order_by('completed_at')
        )

        clusters: dict[str, list[Transaction]] = {}
        for tx in base_qs:
            key = _normalize_description(tx.description)
            if not key:
                continue
            clusters.setdefault(key, []).append(tx)

        items: list[dict] = []
        ai_candidates: list[dict] = []
        for cluster_label, txs in clusters.items():
            if len(txs) < SUBSCRIPTION_MIN_OCCURRENCES:
                continue

            amounts = [abs(float(t.amount)) for t in txs]
            dates = [t.completed_at for t in txs]
            if len(dates) < 2:
                continue

            intervals = [
                (dates[i] - dates[i - 1]).total_seconds() / 86400.0
                for i in range(1, len(dates))
            ]
            intervals = [d for d in intervals if d > 0.1]
            if len(intervals) < SUBSCRIPTION_MIN_INTERVALS:
                continue

            med_amount = _median(amounts)
            med_interval = _median(intervals)
            if med_amount <= 0 or med_interval <= 0:
                continue

            amount_mad_ratio = _safe_ratio(_mad(amounts, med_amount), med_amount)
            interval_mad_ratio = _safe_ratio(_mad(intervals, med_interval), med_interval)
            score = _pattern_score(len(txs), amount_mad_ratio, interval_mad_ratio)
            if score < 0.18:
                continue

            cadence = _classify_cadence(med_interval)
            last_charge = dates[-1]
            first_charge = dates[0]
            next_expected = last_charge + timedelta(days=med_interval)

            overdue_cutoff = last_charge + timedelta(days=med_interval * 1.5)
            is_active = now <= overdue_cutoff

            monthly_equivalent = med_amount * (30.0 / med_interval)
            total_paid = sum(amounts)

            latest = txs[-1]
            cluster_key = _cluster_key_hash(request.user.id, cluster_label)
            item = {
                'cluster_key': cluster_key,
                'cluster_label': cluster_label,
                'merchant': latest.description,
                'category': latest.category.name if latest.category else None,
                'color': latest.category.color if latest.category else '#6B7280',
                'cadence': cadence,
                'avg_amount': round(float(med_amount), 2),
                'avg_interval_days': round(float(med_interval), 1),
                'occurrences': len(txs),
                'first_charge': first_charge.isoformat(),
                'last_charge': last_charge.isoformat(),
                'next_expected': next_expected.isoformat(),
                'total_paid': round(float(total_paid), 2),
                'monthly_equivalent': round(float(monthly_equivalent), 2),
                'is_active': is_active,
                'pattern_score': score,
                'amount_mad_ratio': round(float(amount_mad_ratio), 3),
                'interval_mad_ratio': round(float(interval_mad_ratio), 3),
                'ai_is_subscription': None,
                'confidence': None,
                'reason': None,
                'review_status': 'proposed',
            }
            items.append(item)

            # Build a compact AI payload. Keep the prompt small to control cost.
            charges = []
            for t in txs[-10:]:
                charges.append({
                    'date': t.completed_at.date().isoformat(),
                    'amount': round(abs(float(t.amount)), 2),
                    'category': t.category.name if t.category else None,
                })
            ai_candidates.append({
                'cluster_key': cluster_key,
                'merchant_examples': sorted({t.description for t in txs[-5:]}),
                'charges': charges,
                'stats': {
                    'occurrences': len(txs),
                    'pattern_score': score,
                    'amount_mad_ratio': round(float(amount_mad_ratio), 3),
                    'interval_mad_ratio': round(float(interval_mad_ratio), 3),
                    'cadence_guess': cadence,
                },
            })

        # AI classification (best-effort). Limit to highest-signal candidates.
        ai_candidates.sort(key=lambda c: (c['stats'].get('pattern_score', 0), c['stats'].get('occurrences', 0)), reverse=True)
        ai_candidates = ai_candidates[:40]
        ai_map = classify_subscription_candidates(
            user_id=request.user.id,
            candidates=ai_candidates,
        )

        for i in items:
            ck = i.get('cluster_key')
            if not ck or ck not in ai_map:
                continue
            r = ai_map[ck]
            i['ai_is_subscription'] = r.get('is_subscription')
            i['confidence'] = r.get('confidence')
            i['reason'] = r.get('reason')
            # Prefer AI frequency if present and valid.
            freq = r.get('frequency')
            if freq in {'weekly', 'monthly', 'quarterly', 'yearly', 'irregular'}:
                i['cadence'] = freq
            if r.get('canonical_merchant'):
                i['merchant'] = r['canonical_merchant']
            # Review status:
            # - confirmed/rejected will come from explicit user feedback
            # - here we provide a triage: proposed vs needs_review vs rejected
            if r.get('is_subscription'):
                i['review_status'] = 'proposed' if (i.get('pattern_score', 0) < 0.35 or (i.get('confidence') or 0) < 0.7) else 'proposed'
            else:
                conf = float(i.get('confidence') or 0)
                pat = float(i.get('pattern_score') or 0)
                i['review_status'] = 'rejected' if (conf >= 0.8 and pat < 0.45) else 'needs_review'

        # Apply explicit user overrides (confirm/reject).
        overrides = {
            o.cluster_key: o
            for o in SubscriptionOverride.objects.filter(user=request.user)
        }
        filtered: list[dict] = []
        for i in items:
            ck = i.get('cluster_key')
            o = overrides.get(ck) if ck else None
            if o and o.decision == SubscriptionOverride.Decision.REJECTED:
                continue
            if o and o.decision == SubscriptionOverride.Decision.CONFIRMED:
                i['review_status'] = 'confirmed'
                if o.canonical_merchant_override:
                    i['merchant'] = o.canonical_merchant_override
            filtered.append(i)
        items = filtered

        active_items = [i for i in items if i['is_active']]
        monthly_total = sum(i['monthly_equivalent'] for i in active_items)
        summary = {
            'active_count': len(active_items),
            'inactive_count': len(items) - len(active_items),
            'monthly_total': round(monthly_total, 2),
            'yearly_projection': round(monthly_total * 12.0, 2),
            'total_paid_12m': round(sum(i['total_paid'] for i in items), 2),
        }

        return Response({'summary': summary, 'items': items})


class SubscriptionsFeedbackView(APIView):
    """Persist user feedback (confirm/reject) for a subscription cluster."""

    def post(self, request):
        data = request.data or {}
        cluster_key = data.get('cluster_key')
        decision = data.get('decision')
        canonical_merchant_override = data.get('canonical_merchant_override')

        if not isinstance(cluster_key, str) or len(cluster_key) != 64:
            return Response({'detail': 'cluster_key invalid'}, status=status.HTTP_400_BAD_REQUEST)

        if decision not in {SubscriptionOverride.Decision.CONFIRMED, SubscriptionOverride.Decision.REJECTED}:
            return Response({'detail': 'decision invalid'}, status=status.HTTP_400_BAD_REQUEST)

        obj, _ = SubscriptionOverride.objects.update_or_create(
            user=request.user,
            cluster_key=cluster_key,
            defaults={
                'decision': decision,
                'canonical_merchant_override': canonical_merchant_override or None,
            },
        )

        return Response({
            'cluster_key': obj.cluster_key,
            'decision': obj.decision,
            'canonical_merchant_override': obj.canonical_merchant_override,
            'updated_at': obj.updated_at.isoformat(),
        })
