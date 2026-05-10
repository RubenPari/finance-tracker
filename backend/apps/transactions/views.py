"""API views for transaction CRUD operations and import batch management.

This module defines Django REST Framework views that expose the following
functionality:

- **Transaction CRUD**: List, retrieve, update (category/notes), and delete
  transactions owned by the authenticated user.
- **Import workflow**: Upload XLSX bank statements, track import batch status,
  view transactions within a batch, and commit staged imports to the database.
- **Pagination and filtering**: Configurable page sizes, full-text search on
  descriptions, date/amount/type/category filtering, and sortable columns.

All views enforce user-level data isolation by filtering queries to
``request.user`` only.
"""

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.pagination import PageNumberPagination
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework.generics import (
    ListAPIView,
    RetrieveAPIView,
    UpdateAPIView,
    DestroyAPIView,
)
from django.shortcuts import get_object_or_404
from django.db import transaction as db_transaction
import logging

from .models import Transaction, ImportBatch, ImportStaging
from .serializers import (
    TransactionSerializer,
    TransactionUpdateSerializer,
    ImportBatchSerializer,
    ImportBatchDetailSerializer,
)
from .filters import TransactionFilter
from .tasks import process_import_xlsx


logger = logging.getLogger(__name__)

class TransactionPagination(PageNumberPagination):
    """Custom pagination for transaction list endpoints.

    Provides 50 items per page by default, with client-configurable page sizes
    up to a maximum of 200.
    """

    page_size = 50
    page_size_query_param = "page_size"
    max_page_size = 200


class TransactionListView(ListAPIView):
    """List all transactions for the authenticated user.

    Supports filtering (``TransactionFilter``), full-text search on description,
    and ordering by date, amount, or description. Results are paginated using
    ``TransactionPagination``.
    """

    serializer_class = TransactionSerializer
    pagination_class = TransactionPagination
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = TransactionFilter
    search_fields = ["description"]
    ordering_fields = ["completed_at", "amount", "description", "category__name"]
    ordering = ["-completed_at"]

    def get_queryset(self):
        """Return the user's own transactions with prefetched category data."""
        return Transaction.objects.filter(user=self.request.user).select_related(
            "category"
        )


class TransactionDetailView(RetrieveAPIView):
    """Retrieve a single transaction by ID for the authenticated user."""

    serializer_class = TransactionSerializer

    def get_queryset(self):
        """Return the user's own transactions with prefetched category data."""
        return Transaction.objects.filter(user=self.request.user).select_related(
            "category"
        )


class TransactionUpdateView(UpdateAPIView):
    """Update a transaction's category and notes.

    Uses ``TransactionUpdateSerializer`` which restricts updates to only the
    ``category`` and ``notes`` fields, keeping financial data immutable.
    """

    serializer_class = TransactionUpdateSerializer

    def get_queryset(self):
        """Return the user's own transactions."""
        return Transaction.objects.filter(user=self.request.user)


class TransactionDeleteView(DestroyAPIView):
    """Delete a transaction belonging to the authenticated user."""

    def get_queryset(self):
        """Return the user's own transactions."""
        return Transaction.objects.filter(user=self.request.user)


class ImportView(APIView):
    """Handle XLSX file uploads for transaction import.

    Accepts a POST request with an uploaded XLSX file, validates the file type,
    creates an ``ImportBatch`` record, and queues an asynchronous Celery task
    (``process_import_xlsx``) to parse and stage the transactions.
    """

    def post(self, request):
        """Upload an XLSX bank statement for asynchronous processing.

        Args:
            request: HTTP request containing a ``file`` multipart field.

        Returns:
            Response: 202 Accepted with the serialized ``ImportBatch`` on success,
                or 400 Bad Request with an error message on validation failure.
        """
        file = request.FILES.get("file")
        if not file:
            return Response(
                {"error": "Nessun file caricato."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Validate file extension — only XLSX is supported
        allowed_extensions = (".xlsx",)
        filename = file.name.lower()
        if not filename.endswith(allowed_extensions):
            return Response(
                {"error": "Formato file non supportato. Carica un file .xlsx."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Create an import batch record to track the async job
        import_batch = ImportBatch.objects.create(
            user=request.user,
            filename=file.name,
            status="PROCESSING",
        )

        # Queue the Celery task with the file content and batch metadata
        task = process_import_xlsx.delay(
            import_batch.id, request.user.id, file.read(), file.name
        )

        # Store the Celery task ID on the batch for status polling
        import_batch.task_id = task.id
        import_batch.save(update_fields=["task_id"])

        return Response(
            ImportBatchSerializer(import_batch).data,
            status=status.HTTP_202_ACCEPTED,
        )


class ImportBatchListView(ListAPIView):
    """List all import batches for the authenticated user."""

    serializer_class = ImportBatchSerializer

    def get_queryset(self):
        """Return the user's own import batches."""
        return ImportBatch.objects.filter(user=self.request.user)


class ImportBatchDetailView(RetrieveAPIView):
    """Retrieve details of a single import batch, including transaction count."""

    serializer_class = ImportBatchDetailSerializer

    def get_queryset(self):
        """Return the user's own import batches."""
        return ImportBatch.objects.filter(user=self.request.user)


class ImportBatchTransactionsView(ListAPIView):
    """List committed transactions belonging to a specific import batch.

    This endpoint currently returns only committed ``Transaction`` records.
    Staged (uncommitted) records from ``ImportStaging`` are not included here;
    a separate endpoint would be needed to surface staging data.
    """

    serializer_class = TransactionSerializer
    pagination_class = TransactionPagination
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = TransactionFilter
    search_fields = ["description"]
    ordering_fields = ["completed_at", "amount", "description", "category__name"]
    ordering = ["-completed_at"]

    def get_queryset(self):
        """Return committed transactions for the specified batch, with categories prefetched."""
        batch_id = self.kwargs["pk"]
        return Transaction.objects.filter(
            user=self.request.user,
            import_batch_id=batch_id,
        ).select_related("category")


class ImportCommitView(APIView):
    """Commit staged transactions from an import batch to the main Transaction table.

    This endpoint implements the second phase of the two-phase import workflow.
    When a user confirms an import, all ``ImportStaging`` records for the batch
    are atomically converted into permanent ``Transaction`` records after a
    final duplicate check. The staging records are then deleted.
    """

    def post(self, request, pk):
        """Commit all staged transactions for the given import batch.

        Performs the following steps atomically:
        1. Validates the batch is in ``STAGED`` status.
        2. Checks that staging records exist.
        3. For each staged item, performs a final duplicate check against the
           main ``Transaction`` table.
        4. Resolves the category from the staged category name.
        5. Creates a ``Transaction`` record for each non-duplicate item.
        6. Updates the batch status to ``COMPLETED``.
        7. Deletes all staging records for the batch.

        Args:
            request: HTTP request.
            pk: Primary key of the ``ImportBatch`` to commit.

        Returns:
            Response: 200 OK with the count of committed transactions on success,
                400 Bad Request if the batch is not staged or has no staging data,
                or 500 Internal Server Error on unexpected failures.
        """
        import_batch = get_object_or_404(ImportBatch, id=pk, user=request.user)

        # Only batches in STAGED status can be committed
        if import_batch.status != 'STAGED':
            return Response(
                {"error": "Il batch non è in stato STAGED. Non può essere confermato."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        staged_items = ImportStaging.objects.filter(import_batch=import_batch)
        if not staged_items.exists():
            return Response(
                {"error": "Nessun dato trovato in staging per questo batch."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            # Wrap all commits in a single atomic transaction for consistency
            with db_transaction.atomic():
                committed_count = 0
                for item in staged_items:
                    # Final duplicate check against the main Transaction table
                    exists = Transaction.objects.filter(
                        user_id=request.user.id,
                        started_at=item.started_at,
                        description=item.description,
                        amount=item.amount,
                    ).exists()

                    if not exists:
                        # Resolve category by name — match user-specific or global categories
                        from apps.categories.models import Category
                        category = Category.objects.filter(name=item.category_name, user__in=[request.user, None]).first()

                        Transaction.objects.create(
                            user_id=request.user.id,
                            started_at=item.started_at,
                            completed_at=item.completed_at,
                            description=item.description,
                            amount=item.amount,
                            fee=item.fee,
                            currency=item.currency,
                            transaction_type=item.transaction_type,
                            state=item.state,
                            balance_after=item.balance_after,
                            category=category,
                            import_batch=import_batch,
                        )
                        committed_count += 1

                # Mark the batch as completed and record the committed count
                import_batch.status = 'COMPLETED'
                import_batch.imported_count = committed_count
                import_batch.save()

                # Remove staging records — no longer needed after commit
                ImportStaging.objects.filter(import_batch=import_batch).delete()

            return Response(
                {"message": f"Importazione completata. {committed_count} transazioni salvate."},
                status=status.HTTP_200_OK,
            )
        except Exception:
            logger.exception(
                "Errore inatteso durante il commit dell'import batch %s per utente %s",
                import_batch.id,
                request.user.id,
            )
            return Response(
                {"error": "Errore interno durante la conferma dell'import."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
