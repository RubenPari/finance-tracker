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

from .models import Transaction, ImportBatch
from .serializers import (
    TransactionSerializer,
    TransactionUpdateSerializer,
    ImportBatchSerializer,
)
from .filters import TransactionFilter
from .tasks import process_import_xlsx


class TransactionPagination(PageNumberPagination):
    page_size = 50
    page_size_query_param = 'page_size'
    max_page_size = 200


class TransactionListView(ListAPIView):
    serializer_class = TransactionSerializer
    pagination_class = TransactionPagination
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = TransactionFilter
    search_fields = ['description']
    ordering_fields = ['completed_at', 'amount', 'description']
    ordering = ['-completed_at']

    def get_queryset(self):
        return Transaction.objects.filter(user=self.request.user).select_related('category')


class TransactionDetailView(RetrieveAPIView):
    serializer_class = TransactionSerializer

    def get_queryset(self):
        return Transaction.objects.filter(user=self.request.user).select_related('category')


class TransactionUpdateView(UpdateAPIView):
    serializer_class = TransactionUpdateSerializer

    def get_queryset(self):
        return Transaction.objects.filter(user=self.request.user)


class TransactionDeleteView(DestroyAPIView):
    def get_queryset(self):
        return Transaction.objects.filter(user=self.request.user)


class ImportView(APIView):
    def post(self, request):
        file = request.FILES.get('file')
        if not file:
            return Response(
                {'error': 'Nessun file caricato.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        allowed_extensions = ('.xlsx',)
        filename = file.name.lower()
        if not filename.endswith(allowed_extensions):
            return Response(
                {'error': 'Formato file non supportato. Carica un file .xlsx.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        import_batch = ImportBatch.objects.create(
            user=request.user,
            filename=file.name,
            status='PROCESSING',
        )

        task = process_import_xlsx.delay(import_batch.id, request.user.id, file.read(), file.name)

        import_batch.task_id = task.id
        import_batch.save(update_fields=['task_id'])

        return Response(
            ImportBatchSerializer(import_batch).data,
            status=status.HTTP_202_ACCEPTED,
        )


class ImportBatchListView(ListAPIView):
    serializer_class = ImportBatchSerializer

    def get_queryset(self):
        return ImportBatch.objects.filter(user=self.request.user)


class ImportBatchDetailView(RetrieveAPIView):
    serializer_class = ImportBatchSerializer

    def get_queryset(self):
        return ImportBatch.objects.filter(user=self.request.user)
