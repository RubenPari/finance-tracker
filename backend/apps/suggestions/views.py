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
    def get(self, request):
        suggestions = generate_ai_suggestions(
            request.user,
            _build_ai_context(request.user),
        )

        if suggestions is None:
            suggestions = _generate_legacy_suggestions(request.user)

        return Response(suggestions)


def _build_ai_context(user):
    """Costruisce contesto anonimizzato e aggregato per l'AI gateway."""
    now = timezone.now()
    six_months_ago = now - relativedelta(months=6)
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    prev_month_start = month_start - relativedelta(months=1)

    # Trend mensili ultimi 6 mesi
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

    monthly_trends = []
    for m in monthly:
        monthly_trends.append({
            'month_label': month_name[m['month'].month] if m['month'] else 'Unknown',
            'total': round(abs(float(m['total'])), 2),
            'count': m['count'],
        })

    # Top categorie per spesa (ultimi 6 mesi)
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
            'name': c['category__name'] or 'Senza categoria',
            'total': round(abs(float(c['total'])), 2),
            'count': c['count'],
        })

    # Confronto mese corrente vs precedente
    current_totals = {}
    for c in Transaction.objects.filter(
        user=user, amount__lt=0,
        completed_at__gte=month_start,
    ).values('category__name').annotate(total=Sum('amount')):
        current_totals[c['category__name'] or 'Senza categoria'] = abs(float(c['total']))

    prev_totals = {}
    for c in Transaction.objects.filter(
        user=user, amount__lt=0,
        completed_at__gte=prev_month_start,
        completed_at__lt=month_start,
    ).values('category__name').annotate(total=Sum('amount')):
        prev_totals[c['category__name'] or 'Senza categoria'] = abs(float(c['total']))

    changes = []
    for name, cur in current_totals.items():
        prev = prev_totals.get(name, 0)
        if prev > 0:
            pct = round(((cur - prev) / prev) * 100, 1)
        else:
            pct = 100.0 if cur > 0 else 0.0
        changes.append({
            'category': name,
            'current': round(cur, 2),
            'previous': round(prev, 2),
            'change_pct': pct,
        })
    changes.sort(key=lambda x: abs(x['change_pct']), reverse=True)

    # Abbonamenti rilevati
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

    # Outlier (spese anomali)
    stats = {}
    for item in Transaction.objects.filter(
        user=user, amount__lt=0,
        completed_at__gte=now - relativedelta(months=6),
    ).values('category__name').annotate(avg=Avg('amount'), std=StdDev('amount')):
        if item['std'] and item['std'] > 0:
            stats[item['category__name'] or 'Senza categoria'] = {
                'avg': abs(float(item['avg'])),
                'std': float(item['std']),
            }

    recent_outliers = []
    months1_ago = now - relativedelta(months=1)
    for tx in Transaction.objects.filter(
        user=user, amount__lt=0,
        completed_at__gte=months1_ago,
    ).select_related('category').order_by('-completed_at')[:20]:
        name = tx.category.name if tx.category else 'Senza categoria'
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
    """Fallback con logica statistica originale."""
    suggestions = []

    biggest_increase = _detect_biggest_increase(user)
    if biggest_increase:
        suggestions.append(biggest_increase)

    subscriptions = _detect_subscriptions(user)
    for sub in subscriptions:
        suggestions.append(sub)

    spending_peaks = _detect_spending_peaks(user)
    if spending_peaks:
        suggestions.append(spending_peaks)

    outliers = _detect_outliers(user)
    for outlier in outliers:
        suggestions.append(outlier)

    return suggestions


# ===== Legacy detection functions (unchanged) =====


def _detect_biggest_increase(user):
    now = datetime.now()
    current_start = now.replace(day=1)
    prev_start = current_start - relativedelta(months=1)
    prev_end = current_start

    current_totals = Transaction.objects.filter(
        user=user, amount__lt=0,
        completed_at__gte=current_start,
        completed_at__lt=current_start + relativedelta(months=1),
    ).values('category__name', 'category__color').annotate(
        total=Sum('amount'),
    )

    if not current_totals:
        return None

    prev_totals_map = {}
    for item in Transaction.objects.filter(
        user=user, amount__lt=0,
        completed_at__gte=prev_start,
        completed_at__lt=prev_end,
    ).values('category__name').annotate(
        total=Sum('amount'),
    ):
        prev_totals_map[item['category__name']] = item['total']

    biggest = None
    biggest_pct = 0

    for c in current_totals:
        name = c['category__name'] or 'Senza categoria'
        cur = abs(float(c['total']))
        prev = abs(float(prev_totals_map.get(name, 0)))
        if prev > 0 and cur > prev:
            pct = ((cur - prev) / prev) * 100
            if pct > biggest_pct:
                biggest_pct = pct
                biggest = {
                    'type': 'biggest_increase',
                    'title': f'Aumento in {name}',
                    'message': (
                        f'Le spese in {name} sono aumentate del {round(pct, 1)}% '
                        f'rispetto al mese scorso (da {prev:.2f}€ a {cur:.2f}€).'
                    ),
                    'category': name,
                    'color': c.get('category__color', '#6B7280'),
                    'current_amount': cur,
                    'previous_amount': prev,
                    'change_pct': round(pct, 1),
                }

    return biggest


def _detect_subscriptions(user):
    three_months_ago = datetime.now() - relativedelta(months=3)

    groups = Transaction.objects.filter(
        user=user,
        amount__lt=0,
        completed_at__gte=three_months_ago,
    ).values('description', 'amount').annotate(
        count=Count('id'),
    ).filter(count__gte=3).order_by('-count')

    suggestions = []
    for g in groups[:5]:
        amount = abs(float(g['amount']))
        suggestions.append({
            'type': 'subscription',
            'title': 'Possibile abbonamento',
            'message': (
                f'"{g["description"]}" appare {g["count"]} volte negli ultimi 3 mesi '
                f'per un totale di {amount * g["count"]:.2f}€. '
                f'Potrebbe essere un abbonamento ricorrente.'
            ),
            'merchant': g['description'],
            'amount': amount,
            'occurrences': g['count'],
        })

    return suggestions


def _detect_spending_peaks(user):
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

    worst = transactions[0]
    day_name = worst['day_of_week'].strftime('%A')

    days_it = {
        'Monday': 'Lunedì', 'Tuesday': 'Martedì', 'Wednesday': 'Mercoledì',
        'Thursday': 'Giovedì', 'Friday': 'Venerdì', 'Saturday': 'Sabato', 'Sunday': 'Domenica',
    }

    return {
        'type': 'spending_peaks',
        'title': 'Picco di spesa',
        'message': (
            f'{days_it.get(day_name, day_name)} è il giorno in cui spendi di più: '
            f'{abs(float(worst["total"])):.2f}€ in {worst["count"]} transazioni.'
        ),
        'day': days_it.get(day_name, day_name),
        'total': abs(float(worst['total'])),
        'count': worst['count'],
    }


def _detect_outliers(user):
    now = datetime.now()
    month_start = now.replace(day=1)

    category_avg = Transaction.objects.filter(
        user=user,
        amount__lt=0,
        completed_at__gte=now - relativedelta(months=6),
    ).values('category__name', 'category__color').annotate(
        avg=Avg('amount'),
        std=StdDev('amount'),
    )

    stats = {}
    for item in category_avg:
        name = item['category__name'] or 'Senza categoria'
        if item['std'] and item['std'] > 0:
            stats[name] = {
                'avg': abs(float(item['avg'])),
                'std': float(item['std']),
                'color': item.get('category__color', '#6B7280'),
            }

    outliers = []
    recent = Transaction.objects.filter(
        user=user,
        amount__lt=0,
        completed_at__gte=now - relativedelta(months=1),
    ).select_related('category')

    for tx in recent:
        name = tx.category.name if tx.category else 'Senza categoria'
        if name in stats:
            s = stats[name]
            tx_amount = abs(float(tx.amount))
            if tx_amount > s['avg'] + 2 * s['std'] and tx_amount > s['avg'] * 2:
                outliers.append({
                    'type': 'outlier',
                    'title': 'Spesa anomala',
                    'message': (
                        f'Transazione di {tx_amount:.2f}€ presso "{tx.description}" '
                        f'in {name}. La media per questa categoria è {s["avg"]:.2f}€.'
                    ),
                    'transaction_id': tx.id,
                    'description': tx.description,
                    'amount': tx_amount,
                    'category': name,
                    'color': s['color'],
                    'average': s['avg'],
                })

    return outliers[:5]
