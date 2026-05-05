from rest_framework import serializers
from .models import Transaction, ImportBatch


class TransactionSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)
    category_color = serializers.CharField(source='category.color', read_only=True)

    class Meta:
        model = Transaction
        fields = (
            'id', 'started_at', 'completed_at', 'description', 'amount',
            'fee', 'currency', 'transaction_type', 'state', 'balance_after',
            'category', 'category_name', 'category_color', 'notes', 'created_at',
        )
        read_only_fields = (
            'id', 'started_at', 'completed_at', 'description', 'amount',
            'fee', 'currency', 'transaction_type', 'state', 'balance_after',
            'created_at',
        )


class TransactionUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transaction
        fields = ('category', 'notes')


class ImportBatchSerializer(serializers.ModelSerializer):
    class Meta:
        model = ImportBatch
        fields = (
            'id', 'filename', 'imported_at', 'total_rows',
            'imported_count', 'skipped_count', 'error_count',
            'task_id', 'status',
        )
        read_only_fields = (
            'id', 'filename', 'imported_at', 'total_rows',
            'imported_count', 'skipped_count', 'error_count',
            'task_id', 'status',
        )
