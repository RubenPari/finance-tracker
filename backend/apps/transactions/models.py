"""Database models for transaction tracking and import management.

This module defines the core data models for the finance tracker:
- ``Transaction``: A financial transaction with amounts, dates, categories, and metadata.
- ``ImportBatch``: A group of transactions imported from a single file upload.
- ``ImportStaging``: Temporary storage for imported transactions awaiting user confirmation.
"""

from django.db import models
from django.conf import settings


class ImportBatch(models.Model):
    """Represents a batch of transactions imported from a single file upload.

    An ``ImportBatch`` tracks the progress and results of a file import operation.
    It starts in ``PENDING`` status, moves to ``PROCESSING`` during parsing, then
    ``STAGED`` when rows are loaded into the staging table, and finally ``COMPLETED``
    or ``FAILED`` based on the outcome.

    Attributes:
        user: The user who initiated the import.
        filename: The original name of the uploaded file.
        imported_at: Timestamp when the batch was created.
        total_rows: Total number of rows found in the uploaded file.
        imported_count: Number of rows successfully staged.
        skipped_count: Number of rows skipped (e.g., duplicates).
        error_count: Number of rows that failed processing.
        task_id: Celery task ID for async processing.
        status: Current status of the import batch.
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='import_batches',
    )
    filename = models.CharField(max_length=255)
    imported_at = models.DateTimeField(auto_now_add=True)
    total_rows = models.IntegerField(default=0)
    imported_count = models.IntegerField(default=0)
    skipped_count = models.IntegerField(default=0)
    error_count = models.IntegerField(default=0)
    task_id = models.CharField(max_length=255, blank=True, null=True)
    status = models.CharField(
        max_length=20,
        choices=[
            ('PENDING', 'In attesa'),
            ('PROCESSING', 'In elaborazione'),
            ('STAGED', 'Caricati in staging'),
            ('COMPLETED', 'Completato'),
            ('FAILED', 'Fallito'),
        ],
        default='PENDING',
    )

    class Meta:
        db_table = 'import_batches'
        ordering = ['-imported_at']

    def __str__(self):
        return f'{self.filename} ({self.imported_at.date()})'


class ImportStaging(models.Model):
    """Temporary holding area for imported transactions awaiting user confirmation.

    Rows parsed from an uploaded file are stored here first (staging) rather than
    being inserted directly into the main ``Transaction`` table. This allows users
    to review, validate, or reject the import before it is committed.

    Attributes:
        user: The user who owns this staged transaction.
        import_batch: The parent import batch this row belongs to.
        started_at: Transaction start timestamp.
        completed_at: Transaction completion timestamp.
        description: Merchant or transaction description.
        amount: Transaction amount (negative for expenses, positive for income).
        fee: Associated fee or commission cost.
        currency: Three-letter ISO currency code.
        transaction_type: Type of transaction (e.g., payment, reload).
        state: Transaction state (e.g., COMPLETATO).
        balance_after: Account balance after this transaction.
        category_name: Suggested category name from auto-categorization.
        row_hash: SHA-256 hash of key fields for duplicate detection.
        is_error: Flag indicating whether this row encountered an error.
        error_message: Error details when processing failed.
        created_at: Timestamp when the staging record was created.
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='import_staging',
    )
    import_batch = models.ForeignKey(
        ImportBatch,
        on_delete=models.CASCADE,
        related_name='staged_transactions',
    )
    started_at = models.DateTimeField()
    completed_at = models.DateTimeField()
    description = models.CharField(max_length=500)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    currency = models.CharField(max_length=3, default='EUR')
    transaction_type = models.CharField(max_length=30)
    state = models.CharField(max_length=30, default='COMPLETATO')
    balance_after = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
    )
    category_name = models.CharField(max_length=100, blank=True, null=True)
    row_hash = models.CharField(max_length=64, blank=True, null=True)
    is_error = models.BooleanField(default=False)
    error_message = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'import_staging'
        indexes = [
            models.Index(fields=['user', 'import_batch']),
            models.Index(fields=['row_hash']),
        ]

    def __str__(self):
        """Return a human-readable representation of the staged transaction."""
        return f'Staged: {self.description} ({self.amount})'


class Transaction(models.Model):
    """Represents a single financial transaction belonging to a user.

    Transactions are the core data model, recording financial activities such as
    payments, reloads, withdrawals, and currency exchanges. Each transaction is
    linked to a user and optionally to a category, notes, and the import batch
    that originated it.

    Attributes:
        user: The user who owns this transaction.
        started_at: Transaction start timestamp.
        completed_at: Transaction completion timestamp.
        description: Merchant or transaction description.
        amount: Transaction amount (negative for expenses, positive for income).
        fee: Associated fee or commission cost.
        currency: Three-letter ISO currency code (default 'EUR').
        transaction_type: Type of transaction, constrained to predefined choices.
        state: Transaction state (default 'COMPLETATO').
        balance_after: Account balance after this transaction.
        category: User-assigned category for budgeting and reporting.
        notes: Free-form notes added by the user.
        import_batch: The import batch that created this transaction, if applicable.
        created_at: Timestamp when the record was created.
    """
    TRANSACTION_TYPES = [
        ('Pagamento con carta', 'Pagamento con carta'),
        ('Pagamento', 'Pagamento'),
        ('Pagamento Revolut', 'Pagamento Revolut'),
        ('Ricarica', 'Ricarica'),
        ('Rimborso su carta', 'Rimborso su carta'),
        ('Prelievo', 'Prelievo'),
        ('Cambia valuta', 'Cambia valuta'),
        ('Addebita', 'Addebita'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='transactions',
    )
    started_at = models.DateTimeField()
    completed_at = models.DateTimeField()
    description = models.CharField(max_length=500)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    currency = models.CharField(max_length=3, default='EUR')
    transaction_type = models.CharField(
        max_length=30,
        choices=TRANSACTION_TYPES,
    )
    state = models.CharField(max_length=30, default='COMPLETATO')
    balance_after = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
    )
    category = models.ForeignKey(
        'categories.Category',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='transactions',
    )
    notes = models.TextField(blank=True)
    import_batch = models.ForeignKey(
        ImportBatch,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='transactions',
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'transactions'
        ordering = ['-completed_at']
        indexes = [
            models.Index(fields=['user', 'completed_at']),
            models.Index(fields=['user', 'category']),
            models.Index(fields=['user', 'description']),
        ]

    def __str__(self):
        return f'{self.description} — {self.amount} {self.currency}'
