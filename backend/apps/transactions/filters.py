import django_filters
from .models import Transaction


class TransactionFilter(django_filters.FilterSet):
    date_from = django_filters.DateTimeFilter(field_name='completed_at', lookup_expr='gte')
    date_to = django_filters.DateTimeFilter(field_name='completed_at', lookup_expr='lte')
    amount_min = django_filters.NumberFilter(field_name='amount', lookup_expr='gte')
    amount_max = django_filters.NumberFilter(field_name='amount', lookup_expr='lte')
    type = django_filters.CharFilter(field_name='transaction_type')
    category = django_filters.NumberFilter(field_name='category_id')
    sign = django_filters.CharFilter(method='filter_sign')

    def filter_sign(self, queryset, name, value):
        if value == 'expense':
            return queryset.filter(amount__lt=0)
        if value == 'income':
            return queryset.filter(amount__gt=0)
        return queryset

    class Meta:
        model = Transaction
        fields = ['transaction_type', 'category', 'currency']
