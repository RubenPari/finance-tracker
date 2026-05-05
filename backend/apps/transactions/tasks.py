from celery import shared_task
from .parser import process_import_sync


@shared_task
def process_import_xlsx(batch_id: int, user_id: int, file_content: bytes, filename: str):
    return process_import_sync(batch_id, user_id, file_content, filename)
