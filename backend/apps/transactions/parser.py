"""Parser and processing logic for Revolut XLSX bank statement imports.

This module handles the full import pipeline for Revolut bank statements:
- Parsing XLSX files into structured DataFrames via ``parse_revolut_xlsx``.
- Auto-categorizing transactions using AI batch categorization or keyword rules.
- Computing row hashes for cross-file duplicate detection.
- Synchronously processing imports into the staging area via ``process_import_sync``.

The import workflow is two-phase: files are first parsed into ``ImportStaging``
records (status ``STAGED``) for user review, then committed to the main
``Transaction`` table via the ``ImportCommitView`` endpoint.
"""

import logging
import pandas as pd
import numpy as np
import hashlib
from io import BytesIO
from decimal import Decimal
from django.db import transaction as db_transaction

from .models import Transaction, ImportBatch, ImportStaging
from apps.categories.models import Category, CategoryRule
from apps.categories.ai_categorization import batch_categorize

logger = logging.getLogger(__name__)

# Allowed file extension for bank statement uploads
ALLOWED_EXTENSION = '.xlsx'
# Expected CSV-style header row for Revolut statement files
EXPECTED_HEADER = 'Tipo,Prodotto,Data di inizio,Data di completamento,Descrizione,Importo,Costo,Valuta,State,Saldo'


def parse_revolut_xlsx(file_content: bytes) -> pd.DataFrame:
    """Parse a Revolut XLSX bank statement into a cleaned DataFrame.

    Revolut exports XLSX files where all CSV data is packed into a single column
    of the first sheet. This function extracts that column, reconstructs the CSV
    text, and re-parses it with proper type coercion for dates and numeric fields.

    The resulting DataFrame is filtered to only include completed transactions
    (``State == 'COMPLETATO'``) and has NaN values replaced with None.

    Args:
        file_content: Raw bytes of the uploaded XLSX file.

    Returns:
        pd.DataFrame: Cleaned DataFrame with columns matching the Revolut statement
            format (Tipo, Descrizione, Importo, Costo, Valuta, State, Saldo, etc.),
            filtered to completed transactions only.

    Raises:
        Exception: Propagates any pandas or file parsing errors to the caller.
    """
    # Read the raw XLSX — Revolut packs CSV rows into a single column
    df_raw = pd.read_excel(BytesIO(file_content), header=0, engine='openpyxl')
    # Extract the first (and only) column containing the CSV-formatted data
    col_header = df_raw.columns[0]
    csv_rows = df_raw[col_header].astype(str)
    # Reconstruct the CSV text from the header and row values
    csv_text = col_header + '\n' + '\n'.join(csv_rows)

    # Re-parse as CSV with explicit type mappings for numeric and date columns
    df = pd.read_csv(
        BytesIO(csv_text.encode('utf-8')),
        dtype={'Importo': float, 'Costo': float, 'Saldo': float},
        parse_dates=['Data di inizio', 'Data di completamento'],
    )
    # Only include transactions that have been completed
    df = df[df['State'] == 'COMPLETATO'].copy()
    # Replace NaN values with Python None for database compatibility
    df = df.replace({np.nan: None})
    return df


def auto_categorize(user, description, description_to_category=None):
    """Categorize a single transaction description using AI or rule-based matching.

    Attempts to assign a category to a transaction based on its description text.
    The categorization strategy has two tiers:

    1. **AI mapping** (preferred): If ``description_to_category`` is provided (a
       dict mapping descriptions to category names from batch AI categorization),
       look up the category directly and fetch it from the database.
    2. **Keyword rules** (fallback): If no AI mapping is available, iterate through
       the user's ``CategoryRule`` entries ordered by priority (highest first) and
       return the first rule whose keyword appears in the description.

    Category lookups include both user-specific categories and global categories
    (``user=None``), allowing shared default categories.

    Args:
        user: The user who owns this transaction.
        description: The transaction description string to categorize.
        description_to_category: Optional dict mapping description strings to
            category names, produced by ``batch_categorize``.

    Returns:
        Category: The matched ``Category`` instance, or ``None`` if no match found.
    """
    if description_to_category is not None:
        # Try AI-provided category mapping first
        cat_name = description_to_category.get(description)
        if cat_name:
            try:
                # Look up category for this user or global (user=None)
                return Category.objects.get(
                    name=cat_name,
                    user__in=[user, None]
                )
            except Category.DoesNotExist:
                pass
        return None

    # Fallback: keyword-based rule matching, ordered by priority (highest first)
    rules = CategoryRule.objects.filter(user=user).select_related('category').order_by('-priority')
    for rule in rules:
        # Case-insensitive keyword substring match
        if rule.keyword.lower() in description.lower():
            return rule.category
    return None


def compute_row_hash(row):
    """Compute a SHA-256 hash of key transaction fields for duplicate detection.

    The hash is computed from the combination of start date, description, amount,
    and currency. This allows detecting duplicate transactions across different
    import files without requiring an exact row match.

    Args:
        row: A DataFrame row (Series) containing the Revolut statement columns.

    Returns:
        str: Hex digest of the SHA-256 hash.
    """
    data = (
        str(row['Data di inizio']),
        str(row['Descrizione']),
        str(row['Importo']),
        str(row['Valuta']),
    )
    return hashlib.sha256(''.join(data).encode('utf-8')).hexdigest()


def process_import_sync(batch_id: int, user_id: int, file_content: bytes, filename: str) -> dict:
    """Synchronously parse an XLSX file and stage its transactions for review.

    This is the core import processing function called by the Celery task
    ``process_import_xlsx``. It performs the following steps:

    1. Parse the XLSX file into a DataFrame using ``parse_revolut_xlsx``.
    2. Run AI batch categorization on all unique transaction descriptions.
    3. Iterate through each row, computing a hash for duplicate detection.
    4. Skip rows that already exist in the main ``Transaction`` table or in
       any ``ImportStaging`` record for this user.
    5. Auto-categorize each new transaction and create an ``ImportStaging`` record.
    6. Update the ``ImportBatch`` with counts and set status to ``STAGED``.

    The entire row processing runs inside a single database transaction to ensure
    consistency. If any fatal error occurs during parsing, the batch status is set
    to ``FAILED``.

    Args:
        batch_id: Primary key of the ``ImportBatch`` to update.
        user_id: Primary key of the user who uploaded the file.
        file_content: Raw bytes of the uploaded XLSX file.
        filename: Original filename (used for logging and batch tracking).

    Returns:
        dict: Summary with keys ``imported`` (staged count), ``skipped`` (duplicates),
            ``errors`` (rows that failed processing), and ``total`` (total rows parsed).

    Raises:
        Exception: Re-raises any fatal parsing error after marking the batch as ``FAILED``.
    """
    import_batch = ImportBatch.objects.get(id=batch_id)
    try:
        # Parse the XLSX file into a structured DataFrame
        df = parse_revolut_xlsx(file_content)

        total_rows = len(df)
        imported = 0
        skipped = 0
        errors = 0

        # Run AI batch categorization on all unique descriptions upfront
        all_descriptions = df['Descrizione'].dropna().astype(str).unique().tolist()
        description_to_category = batch_categorize(import_batch.user, all_descriptions)

        # Process each row within a single database transaction
        with db_transaction.atomic():
            for _, row in df.iterrows():
                try:
                    # Extract and coerce fields from the DataFrame row
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

                    # Compute hash for cross-file duplicate detection
                    row_hash = compute_row_hash(row)

                    # Check if this transaction already exists in the main table
                    exists_in_main = Transaction.objects.filter(
                        user_id=user_id,
                        started_at=started_at,
                        description=description,
                        amount=amount,
                    ).exists()

                    # Check if already staged in a pending import batch
                    exists_in_staging = ImportStaging.objects.filter(
                        user_id=user_id,
                        row_hash=row_hash,
                    ).exists()

                    if exists_in_main or exists_in_staging:
                        skipped += 1
                        continue

                    # Auto-categorize using AI mapping or keyword rule fallback
                    category = auto_categorize(
                        import_batch.user,
                        description,
                        description_to_category=description_to_category,
                    )

                    category_name = category.name if category else None

                    # Store in staging table for user review before committing
                    ImportStaging.objects.create(
                        user_id=user_id,
                        import_batch=import_batch,
                        started_at=started_at,
                        completed_at=completed_at,
                        description=description,
                        amount=amount,
                        fee=fee,
                        currency=currency,
                        transaction_type=transaction_type,
                        state=state,
                        balance_after=balance_after,
                        category_name=category_name,
                        row_hash=row_hash,
                    )
                    imported += 1
                except Exception as e:
                    # Log individual row failures but continue processing
                    logger.warning('Failed to process row during import: %s', e)
                    errors += 1

        # Update batch summary and mark as staged for review
        import_batch.total_rows = total_rows
        import_batch.imported_count = imported
        import_batch.skipped_count = skipped
        import_batch.error_count = errors
        import_batch.status = 'STAGED'
        import_batch.save()

        return {
            'imported': imported,
            'skipped': skipped,
            'errors': errors,
            'total': total_rows,
        }
    except Exception as e:
        # Mark batch as failed on any fatal error
        import_batch.status = 'FAILED'
        import_batch.save()
        raise e
