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
