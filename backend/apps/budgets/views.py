from rest_framework import status
from rest_framework.response import Response
from rest_framework.generics import (
    ListAPIView,
    CreateAPIView,
    UpdateAPIView,
    DestroyAPIView,
)
from django_filters.rest_framework import DjangoFilterBackend

from .models import Budget
from .serializers import BudgetSerializer


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
        return Budget.objects.filter(user=self.request.user).select_related('category')


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
