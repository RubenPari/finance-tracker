from django.db import models
from django.conf import settings


class ImportBatch(models.Model):
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
        return f'Staged: {self.description} ({self.amount})'


class Transaction(models.Model):
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
