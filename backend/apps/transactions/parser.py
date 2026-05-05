import pandas as pd
import numpy as np
from io import BytesIO
from decimal import Decimal
from django.db import transaction as db_transaction

from .models import Transaction, ImportBatch
from apps.categories.models import Category, CategoryRule
from apps.categories.ai_categorization import batch_categorize


ALLOWED_EXTENSION = '.xlsx'
EXPECTED_HEADER = 'Tipo,Prodotto,Data di inizio,Data di completamento,Descrizione,Importo,Costo,Valuta,State,Saldo'


def parse_revolut_xlsx(file_content: bytes) -> pd.DataFrame:
    df_raw = pd.read_excel(BytesIO(file_content), header=0, engine='openpyxl')
    col_header = df_raw.columns[0]
    csv_rows = df_raw[col_header].astype(str)
    csv_text = col_header + '\n' + '\n'.join(csv_rows)

    df = pd.read_csv(
        BytesIO(csv_text.encode('utf-8')),
        dtype={'Importo': float, 'Costo': float, 'Saldo': float},
        parse_dates=['Data di inizio', 'Data di completamento'],
    )
    df = df[df['State'] == 'COMPLETATO'].copy()
    df = df.replace({np.nan: None})
    return df


def auto_categorize(user, description, description_to_category=None):
    """
    Categorize a single transaction description.
    
    If description_to_category mapping is provided, uses it directly.
    Otherwise falls back to keyword matching via CategoryRule.
    """
    if description_to_category is not None:
        cat_name = description_to_category.get(description)
        if cat_name:
            try:
                return Category.objects.get(
                    name=cat_name,
                    user__in=[user, None]  # user=None means system category
                )
            except Category.DoesNotExist:
                pass
        return None

    # Legacy keyword fallback
    rules = CategoryRule.objects.filter(user=user).select_related('category').order_by('-priority')
    for rule in rules:
        if rule.keyword.lower() in description.lower():
            return rule.category
    return None


def process_import_sync(batch_id: int, user_id: int, file_content: bytes, filename: str) -> dict:
    import_batch = ImportBatch.objects.get(id=batch_id)
    try:
        df = parse_revolut_xlsx(file_content)

        total_rows = len(df)
        imported = 0
        skipped = 0
        errors = 0

        # AI Batch categorization: extract unique descriptions first
        all_descriptions = df['Descrizione'].dropna().astype(str).unique().tolist()
        description_to_category = batch_categorize(import_batch.user, all_descriptions)

        with db_transaction.atomic():
            for _, row in df.iterrows():
                try:
                    started_at = row['Data di inizio']
                    completed_at = row['Data di completamento']
                    description = str(row['Descrizione'])
                    amount = Decimal(str(row['Importo']))
                    fee = Decimal(str(row.get('Costo', 0) or 0))
                    currency = str(row['Valuta'])
                    transaction_type = str(row['Tipo'])
                    state = str(row['State'])
                    balance_val = row.get('Saldo')
                    balance_after = Decimal(str(balance_val)) if balance_val is not None else None

                    exists = Transaction.objects.filter(
                        user_id=user_id,
                        started_at=started_at,
                        description=description,
                        amount=amount,
                    ).exists()

                    if exists:
                        skipped += 1
                        continue

                    category = auto_categorize(
                        import_batch.user,
                        description,
                        description_to_category=description_to_category,
                    )

                    Transaction.objects.create(
                        user_id=user_id,
                        started_at=started_at,
                        completed_at=completed_at,
                        description=description,
                        amount=amount,
                        fee=fee,
                        currency=currency,
                        transaction_type=transaction_type,
                        state=state,
                        balance_after=balance_after,
                        category=category,
                        import_batch=import_batch,
                    )
                    imported += 1
                except Exception:
                    errors += 1

        import_batch.total_rows = total_rows
        import_batch.imported_count = imported
        import_batch.skipped_count = skipped
        import_batch.error_count = errors
        import_batch.status = 'COMPLETED'
        import_batch.save()

        return {
            'imported': imported,
            'skipped': skipped,
            'errors': errors,
            'total': total_rows,
        }
    except Exception as e:
        import_batch.status = 'FAILED'
        import_batch.save()
        raise e
