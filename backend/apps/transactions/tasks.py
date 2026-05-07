"""Celery asynchronous tasks for transaction import processing.

This module defines Celery shared tasks that handle file imports in the background,
allowing users to upload large bank statements without blocking the HTTP request.
Tasks include file parsing, duplicate detection, auto-categorization, and cache
invalidation for AI-generated suggestions.
"""

from celery import shared_task
from django.contrib.auth import get_user_model
from .parser import process_import_sync
from apps.suggestions.ai_service import invalidate_suggestions_cache

User = get_user_model()


@shared_task
def process_import_xlsx(batch_id: int, user_id: int, file_content: bytes, filename: str):
    """Process an uploaded XLSX file and stage its transactions for review.

    This task runs asynchronously via Celery. It parses the file into staging
    records (``ImportStaging``), performs duplicate detection against existing
    transactions and other pending batches, and applies AI-assisted categorization.
    After successful staging, it invalidates the user's AI suggestion cache so
    that future recommendations reflect the new data.

    Args:
        batch_id: Primary key of the ``ImportBatch`` tracking this import.
        user_id: Primary key of the user who uploaded the file.
        file_content: Raw bytes of the uploaded XLSX file.
        filename: Original filename of the uploaded file.

    Returns:
        dict: A dictionary with keys ``imported``, ``skipped``, ``errors``, and
            ``total``, summarizing the processing results.

    Side effects:
        - Creates ``ImportStaging`` records for each new transaction row.
        - Updates the ``ImportBatch`` status to ``STAGED`` or ``FAILED``.
        - Invalidates the user's AI suggestions cache upon success.
    """
    # Parse file into staging area (sets batch status to STAGED)
    result = process_import_sync(batch_id, user_id, file_content, filename)
    # Invalidate cached AI suggestions so they reflect the newly imported data
    try:
        user = User.objects.get(pk=user_id)
        invalidate_suggestions_cache(user)
    except User.DoesNotExist:
        pass
    return result
