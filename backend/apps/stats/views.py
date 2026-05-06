from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.db.models import Sum, Count, Q
from datetime import datetime, timedelta, date
from dateutil.relativedelta import relativedelta

from apps.transactions.models import Transaction


def get_date_range(request):
    now = datetime.now()
    period = request.query_params.get('period', 'month')
    date_from_str = request.query_params.get('date_from')
    date_to_str = request.query_params.get('date_to')

    if date_from_str and date_to_str:
        date_from = datetime.strptime(date_from_str, '%Y-%m-%d')
        date_to = datetime.strptime(date_to_str, '%Y-%m-%d')
        date_to = date_to + timedelta(days=1)
        prev_months = 1
    elif period == 'year':
        date_from = now.replace(month=1, day=1)
        date_to = date_from + relativedelta(years=1)
        prev_months = 12
    elif period == 'quarter':
        month = ((now.month - 1) // 3) * 3 + 1
        date_from = now.replace(month=month, day=1)
        date_to = date_from + relativedelta(months=3)
        prev_months = 3
    else:
        date_from = now.replace(day=1)
        date_to = date_from + relativedelta(months=1)
        prev_months = 1

    return date_from, date_to, prev_months


class SummaryView(APIView):
    def get(self, request):
        date_from, date_to, _ = get_date_range(request)

        qs = Transaction.objects.filter(
            user=request.user,
            completed_at__gte=date_from,
            completed_at__lt=date_to,
        )

        aggregates = qs.aggregate(
            total_expenses=Sum('amount', filter=Q(amount__lt=0)),
            total_income=Sum('amount', filter=Q(amount__gt=0)),
            count=Count('id'),
        )

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
    def get(self, request):
        date_from, date_to, _ = get_date_range(request)

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
            'total': abs(float(item['total'])),
            'count': item['count'],
        } for item in data])


class MonthlyTrendView(APIView):
    def get(self, request):
        months = int(request.query_params.get('months', 12))

        result = []
        current = datetime.now().replace(day=1)

        for i in range(months):
            period_start = current - relativedelta(months=months - 1 - i)
            period_end = period_start + relativedelta(months=1)

            qs = Transaction.objects.filter(
                user=request.user,
                completed_at__gte=period_start,
                completed_at__lt=period_end,
            )

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
    def get(self, request):
        date_from, date_to, _ = get_date_range(request)
        limit = int(request.query_params.get('limit', 5))

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
    def get(self, request):
        transactions = Transaction.objects.filter(
            user=request.user,
            balance_after__isnull=False,
        ).order_by('completed_at').values('completed_at', 'balance_after')

        return Response([{
            'date': t['completed_at'].isoformat(),
            'balance': float(t['balance_after']),
        } for t in transactions])


class ComparisonView(APIView):
    def get(self, request):
        date_from, date_to, prev_months = get_date_range(request)
        prev_from = date_from - timedelta(days=prev_months * 30)
        prev_to = date_from

        current = Transaction.objects.filter(
            user=request.user,
            amount__lt=0,
            completed_at__gte=date_from,
            completed_at__lt=date_to,
        ).values('category__name', 'category__color').annotate(
            total=Sum('amount'),
        )

        previous = Transaction.objects.filter(
            user=request.user,
            amount__lt=0,
            completed_at__gte=prev_from,
            completed_at__lt=prev_to,
        ).values('category__name').annotate(
            total=Sum('amount'),
        )

        prev_map = {p['category__name']: p['total'] for p in previous}

        return Response([{
            'category': c['category__name'] or 'Senza categoria',
            'color': c['category__color'] or '#6B7280',
            'current': abs(float(c['total'])),
            'previous': abs(float(prev_map.get(c['category__name'], 0))),
            'change_pct': round(
                ((abs(float(c['total'])) - abs(float(prev_map.get(c['category__name'], 0))))
                 / max(abs(float(prev_map.get(c['category__name'], 1))), 1)) * 100, 1
            ) if prev_map.get(c['category__name']) else None,
        } for c in current])
