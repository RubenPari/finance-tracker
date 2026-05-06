from django.urls import path
from . import views

urlpatterns = [
    path("", views.TransactionListView.as_view(), name="transaction-list"),
    path("import/", views.ImportView.as_view(), name="transaction-import"),
    path(
        "import/history/", views.ImportBatchListView.as_view(), name="import-batch-list"
    ),
    path(
        "import/<int:pk>/",
        views.ImportBatchDetailView.as_view(),
        name="import-batch-detail",
    ),
    path(
        "import/<int:pk>/transactions/",
        views.ImportBatchTransactionsView.as_view(),
        name="import-batch-transactions",
    ),
    path("<int:pk>/", views.TransactionDetailView.as_view(), name="transaction-detail"),
    path(
        "<int:pk>/update/",
        views.TransactionUpdateView.as_view(),
        name="transaction-update",
    ),
    path(
        "<int:pk>/delete/",
        views.TransactionDeleteView.as_view(),
        name="transaction-delete",
    ),
]
