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

from .models import Transaction, ImportBatch, ImportStaging
from .serializers import (
    TransactionSerializer,
    TransactionUpdateSerializer,
    ImportBatchSerializer,
    ImportBatchDetailSerializer,
)
from .filters import TransactionFilter
from .tasks import process_import_xlsx

class TransactionPagination(PageNumberPagination):
    page_size = 50
    page_size_query_param = "page_size"
    max_page_size = 200


class TransactionListView(ListAPIView):
    serializer_class = TransactionSerializer
    pagination_class = TransactionPagination
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = TransactionFilter
    search_fields = ["description"]
    ordering_fields = ["completed_at", "amount", "description"]
    ordering = ["-completed_at"]

    def get_queryset(self):
        return Transaction.objects.filter(user=self.request.user).select_related(
            "category"
        )


class TransactionDetailView(RetrieveAPIView):
    serializer_class = TransactionSerializer

    def get_queryset(self):
        return Transaction.objects.filter(user=self.request.user).select_related(
            "category"
        )


class TransactionUpdateView(UpdateAPIView):
    serializer_class = TransactionUpdateSerializer

    def get_queryset(self):
        return Transaction.objects.filter(user=self.request.user)


class TransactionDeleteView(DestroyAPIView):
    def get_queryset(self):
        return Transaction.objects.filter(user=self.request.user)


class ImportView(APIView):
    def post(self, request):
        file = request.FILES.get("file")
        if not file:
            return Response(
                {"error": "Nessun file caricato."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        allowed_extensions = (".xlsx",)
        filename = file.name.lower()
        if not filename.endswith(allowed_extensions):
            return Response(
                {"error": "Formato file non supportato. Carica un file .xlsx."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        import_batch = ImportBatch.objects.create(
            user=request.user,
            filename=file.name,
            status="PROCESSING",
        )

        task = process_import_xlsx.delay(
            import_batch.id, request.user.id, file.read(), file.name
        )

        import_batch.task_id = task.id
        import_batch.save(update_fields=["task_id"])

        return Response(
            ImportBatchSerializer(import_batch).data,
            status=status.HTTP_202_ACCEPTED,
        )


class ImportBatchListView(ListAPIView):
    serializer_class = ImportBatchSerializer

    def get_queryset(self):
        return ImportBatch.objects.filter(user=self.request.user)


class ImportBatchDetailView(RetrieveAPIView):
    serializer_class = ImportBatchDetailSerializer

    def get_queryset(self):
        return ImportBatch.objects.filter(user=self.request.user)


class ImportBatchTransactionsView(ListAPIView):
    serializer_class = TransactionSerializer
    pagination_class = TransactionPagination
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = TransactionFilter
    search_fields = ["description"]
    ordering_fields = ["completed_at", "amount", "description"]
    ordering = ["-completed_at"]

    def get_queryset(self):
        batch_id = self.kwargs["pk"]
        # We now support both committed transactions and staged ones
        # This is a simplified view; in a real app we might have a separate StagingTransactionSerializer
        # For now, let's keep it looking at Transactions.
        # To actually see staged data, the user would need a new endpoint.
        return Transaction.objects.filter(
            user=self.request.user,
            import_batch_id=batch_id,
        ).select_related("category")


class ImportCommitView(APIView):
    def post(self, request, batch_id):
        import_batch = get_object_or_404(ImportBatch, id=batch_id, user=request.user)

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
            with db_transaction.atomic():
                committed_count = 0
                for item in staged_items:
                    # Final duplicate check against main Transaction table
                    exists = Transaction.objects.filter(
                        user_id=request.user.id,
                        started_at=item.started_at,
                        description=item.description,
                        amount=item.amount,
                    ).exists()

                    if not exists:
                        # Resolve category
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

                # Update batch status and cleanup
                import_batch.status = 'COMPLETED'
                import_batch.imported_count = committed_count
                import_batch.save()

                # Cleanup staging
                ImportStaging.objects.filter(import_batch=import_batch).delete()

            return Response(
                {"message": f"Importazione completata. {committed_count} transazioni salvate."},
                status=status.HTTP_200_OK,
            )
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
