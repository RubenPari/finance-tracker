from rest_framework import serializers
from .models import Budget


class BudgetSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)
    category_color = serializers.CharField(source='category.color', read_only=True)
    current_spent = serializers.SerializerMethodField()
    percentage = serializers.SerializerMethodField()

    class Meta:
        model = Budget
        fields = (
            'id', 'category', 'category_name', 'category_color',
            'year', 'month', 'amount_limit', 'current_spent', 'percentage',
        )
        read_only_fields = ('id',)

    def get_current_spent(self, obj):
        from django.db.models import Sum
        from apps.transactions.models import Transaction
        import datetime

        start_date = datetime.date(obj.year, obj.month, 1)
        if obj.month == 12:
            end_date = datetime.date(obj.year + 1, 1, 1)
        else:
            end_date = datetime.date(obj.year, obj.month + 1, 1)

        spent = Transaction.objects.filter(
            user=obj.user,
            category=obj.category,
            amount__lt=0,
            completed_at__gte=start_date,
            completed_at__lt=end_date,
        ).aggregate(total=Sum('amount'))['total']

        return abs(float(spent or 0))

    def get_percentage(self, obj):
        current = self.get_current_spent(obj)
        limit = float(obj.amount_limit)
        if limit == 0:
            return 0
        return round((current / limit) * 100, 1)
