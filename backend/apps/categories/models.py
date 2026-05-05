from django.db import models
from django.conf import settings


class Category(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='categories',
    )
    name = models.CharField(max_length=100)
    color = models.CharField(max_length=7, default='#6B7280')
    icon = models.CharField(max_length=50, default='category')
    is_system = models.BooleanField(default=False)

    class Meta:
        db_table = 'categories'
        unique_together = [('user', 'name')]

    def __str__(self):
        return self.name


class CategoryRule(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='category_rules',
    )
    keyword = models.CharField(max_length=255)
    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        related_name='rules',
    )
    priority = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'category_rules'
        ordering = ['-priority', 'created_at']

    def __str__(self):
        return f'"{self.keyword}" → {self.category.name}'
