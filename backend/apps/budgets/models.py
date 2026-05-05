from django.db import models
from django.conf import settings


class Budget(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='budgets',
    )
    category = models.ForeignKey(
        'categories.Category',
        on_delete=models.CASCADE,
        related_name='budgets',
    )
    year = models.IntegerField()
    month = models.IntegerField()
    amount_limit = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        db_table = 'budgets'
        unique_together = [('user', 'category', 'year', 'month')]
        ordering = ['-year', '-month']

    def __str__(self):
        return f'{self.category.name} {self.month:02d}/{self.year}: {self.amount_limit}€'
