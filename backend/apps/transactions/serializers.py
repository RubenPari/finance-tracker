"""Serializers for transaction and import batch data.

This module defines Django REST Framework serializers that handle:
- Serializing ``Transaction`` instances for API responses, including nested
  category data (name and color).
- Deserializing partial updates for transactions (category and notes only).
- Serializing ``ImportBatch`` instances for tracking import job status.
"""

from rest_framework import serializers
from .models import Transaction, ImportBatch


class TransactionSerializer(serializers.ModelSerializer):
    """Serializes a full Transaction for read-only API responses.

    Includes nested category fields (``category_name`` and ``category_color``)
    flattened from the related ``Category`` model for convenience. Most fields
    are read-only since transactions are immutable after import.
    """
    category_name = serializers.CharField(source="category.name", read_only=True)
    category_color = serializers.CharField(source="category.color", read_only=True)

    class Meta:
        model = Transaction
        fields = (
            "id",
            "started_at",
            "completed_at",
            "description",
            "amount",
            "fee",
            "currency",
            "transaction_type",
            "state",
            "balance_after",
            "category",
            "category_name",
            "category_color",
            "notes",
            "created_at",
        )
        read_only_fields = (
            "id",
            "started_at",
            "completed_at",
            "description",
            "amount",
            "fee",
            "currency",
            "transaction_type",
            "state",
            "balance_after",
            "created_at",
        )


class TransactionUpdateSerializer(serializers.ModelSerializer):
    """Serializes partial updates for a Transaction.

    Only allows updating ``category`` and ``notes`` fields, since transaction
    financial data (amount, date, description) should remain immutable after import.
    """

    class Meta:
        model = Transaction
        fields = ("category", "notes")


class ImportBatchSerializer(serializers.ModelSerializer):
    """Serializes an ImportBatch for list and summary responses.

    All fields are read-only, providing import job metadata such as status,
    row counts, and the Celery task ID.
    """

    class Meta:
        model = ImportBatch
        fields = (
            "id",
            "filename",
            "imported_at",
            "total_rows",
            "imported_count",
            "skipped_count",
            "error_count",
            "task_id",
            "status",
        )
        read_only_fields = (
            "id",
            "filename",
            "imported_at",
            "total_rows",
            "imported_count",
            "skipped_count",
            "error_count",
            "task_id",
            "status",
        )


class ImportBatchDetailSerializer(serializers.ModelSerializer):
    """Serializes an ImportBatch with additional detail for single-batch views.

    Extends the base batch serializer with a ``transactions_count`` field that
    computes the number of committed transactions linked to this batch.
    """
    transactions_count = serializers.SerializerMethodField()

    class Meta:
        model = ImportBatch
        fields = (
            "id",
            "filename",
            "imported_at",
            "total_rows",
            "imported_count",
            "skipped_count",
            "error_count",
            "task_id",
            "status",
            "transactions_count",
        )
        read_only_fields = fields

    def get_transactions_count(self, obj):
        """Return the number of committed transactions linked to this import batch.

        Args:
            obj: The ImportBatch instance being serialized.

        Returns:
            int: Count of related Transaction records.
        """
        return obj.transactions.count()
