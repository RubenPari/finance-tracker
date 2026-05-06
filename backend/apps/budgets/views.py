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
    def filter_queryset(self, request, queryset, view):
        year = request.query_params.get('year')
        month = request.query_params.get('month')
        if year:
            queryset = queryset.filter(year=year)
        if month:
            queryset = queryset.filter(month=month)
        return queryset


class BudgetListView(ListAPIView):
    serializer_class = BudgetSerializer
    filter_backends = [BudgetFilter]

    def get_queryset(self):
        now = timezone.now()
        year = int(self.request.query_params.get('year', now.year))
        month = int(self.request.query_params.get('month', now.month))

        start_date = date(year, month, 1)
        end_date = date(year + 1, 1, 1) if month == 12 else date(year, month + 1, 1)

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
        queryset = self.get_queryset()
        for budget in queryset:
            budget._current_spent = abs(float(budget._spent or 0))
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class BudgetCreateView(CreateAPIView):
    serializer_class = BudgetSerializer

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class BudgetUpdateView(UpdateAPIView):
    serializer_class = BudgetSerializer

    def get_queryset(self):
        return Budget.objects.filter(user=self.request.user)


class BudgetDeleteView(DestroyAPIView):
    def get_queryset(self):
        return Budget.objects.filter(user=self.request.user)
