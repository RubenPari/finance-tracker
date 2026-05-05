from celery import shared_task
from django.contrib.auth import get_user_model
from .parser import process_import_sync
from apps.suggestions.ai_service import invalidate_suggestions_cache

User = get_user_model()


@shared_task
def process_import_xlsx(batch_id: int, user_id: int, file_content: bytes, filename: str):
    result = process_import_sync(batch_id, user_id, file_content, filename)
    try:
        user = User.objects.get(pk=user_id)
        invalidate_suggestions_cache(user)
    except User.DoesNotExist:
        pass
    return result
