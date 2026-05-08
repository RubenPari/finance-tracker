from __future__ import annotations

from django.conf import settings
from django.db import models


class SubscriptionOverride(models.Model):
    class Decision(models.TextChoices):
        CONFIRMED = 'CONFIRMED', 'Confirmed'
        REJECTED = 'REJECTED', 'Rejected'

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='subscription_overrides',
    )
    # Deterministic key returned by the subscriptions endpoint.
    cluster_key = models.CharField(max_length=64)
    decision = models.CharField(max_length=20, choices=Decision.choices)
    canonical_merchant_override = models.CharField(max_length=255, blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'subscription_overrides'
        unique_together = ('user', 'cluster_key')
        indexes = [
            models.Index(fields=['user', 'cluster_key']),
            models.Index(fields=['user', 'decision']),
        ]

    def __str__(self) -> str:
        return f'{self.user_id}:{self.cluster_key}={self.decision}'

