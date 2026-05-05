from django.db import models
from rest_framework import status
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


class CategoryListView(ListAPIView):
    serializer_class = CategorySerializer
    pagination_class = None

    def get_queryset(self):
        return Category.objects.filter(
            models.Q(user=self.request.user) | models.Q(is_system=True),
        )


class CategoryCreateView(CreateAPIView):
    serializer_class = CategorySerializer

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class CategoryUpdateView(UpdateAPIView):
    serializer_class = CategorySerializer

    def get_queryset(self):
        return Category.objects.filter(user=self.request.user, is_system=False)


class CategoryDeleteView(DestroyAPIView):
    def get_queryset(self):
        return Category.objects.filter(user=self.request.user, is_system=False)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        fallback = Category.objects.filter(is_system=True, name='Altro').first()
        Transaction.objects.filter(category=instance).update(category=fallback)
        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)


class CategoryRuleListView(ListAPIView):
    serializer_class = CategoryRuleSerializer

    def get_queryset(self):
        return CategoryRule.objects.filter(user=self.request.user).select_related('category')


class CategoryRuleCreateView(CreateAPIView):
    serializer_class = CategoryRuleSerializer

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class CategoryRuleDeleteView(DestroyAPIView):
    def get_queryset(self):
        return CategoryRule.objects.filter(user=self.request.user)


class AICategorizeView(APIView):
    """
    POST /api/categories/ai-categorize/
    Categorizes all uncategorized transactions for the user using AI Gateway.
    Query params: ?limit=100 (default)
    Returns count of categorized transactions and category assignments.
    """
    def post(self, request, *args, **kwargs):
        limit = int(request.query_params.get('limit', 100))

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

        # Extract unique descriptions
        unique_descs = list({tx.description for tx in uncategorized})

        # AI Batch categorize
        mapping = batch_categorize(request.user, unique_descs)

        # Build category name -> Category object lookup
        cat_name_to_obj = {}
        for cat in Category.objects.filter(
            models.Q(user=request.user) | models.Q(is_system=True)
        ):
            cat_name_to_obj[cat.name] = cat

        categorized_count = 0
        assignments = []
        for tx in uncategorized:
            cat_name = mapping.get(tx.description)
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
