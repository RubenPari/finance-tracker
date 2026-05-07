"""
AI-powered transaction categorization service.

Provides intelligent automatic categorization of bank transactions using
an external AI Gateway API, with a keyword-based fallback system and
Django cache layer for performance optimization.

Categorization flow:
    1. Check Django cache for previously categorized descriptions
    2. Send uncached descriptions to the AI Gateway in batches
    3. Cache AI results for future lookups (30-day TTL)
    4. If AI fails or is disabled, fall back to keyword rule matching
"""

import json
import hashlib
from typing import Optional
from django.conf import settings
from django.core.cache import cache
from django.db.models import Q

from apps.suggestions.ai_service import call_ai_gateway
from apps.categories.models import Category, CategoryRule
from apps.utils import strip_markdown


# Feature flag: when False, skip AI and use keyword matching only
AI_CATEGORIZATION_ENABLED = getattr(settings, 'AI_CATEGORIZATION_ENABLED', True)
# Maximum number of descriptions to send in a single AI Gateway request
AI_CATEGORIZATION_BATCH_SIZE = getattr(settings, 'AI_CATEGORIZATION_BATCH_SIZE', 20)
# Timeout in seconds for each AI Gateway API call
AI_CATEGORIZATION_TIMEOUT = getattr(settings, 'AI_CATEGORIZATION_TIMEOUT', 15)
# Cache time-to-live in seconds for categorization results (30 days)
AI_CATEGORIZATION_CACHE_TTL = getattr(settings, 'AI_CATEGORIZATION_CACHE_TTL', 2592000)  # 30 days

# System prompt sent to the AI Gateway to instruct it on categorization behavior.
# Requests a strict JSON mapping from transaction descriptions to category names,
# with 'Altro' as the fallback for uncertain classifications.
_CATEGORIZATION_SYSTEM_PROMPT = (
    "Sei un classificatore di transazioni bancarie. "
    "Data una lista di descrizioni transazione e una lista di categorie disponibili, "
    "restituisci il mapping esatto descrizione \u2192 categoria in formato JSON rigoroso. "
    "Ogni oggetto deve avere i campi: description (string), category (string). "
    "Usa ESATTAMENTE i nomi delle categorie fornite. "
    "Se non sei sicuro, usa sempre 'Altro' come fallback. "
    "Non aggiungere spiegazioni, restituisci SOLO il JSON."
)


def _build_categorization_prompt(descriptions: list[str], categories: list[str]) -> str:
    """Build the user prompt for the AI categorization request.

    Formats the available categories and transaction descriptions into a
    structured prompt that instructs the AI to return a JSON array mapping
    each description to its best-matching category.

    Args:
        descriptions: List of transaction description strings to categorize.
        categories: List of available category name strings the AI can choose from.

    Returns:
        A formatted prompt string containing categories, descriptions, and
        JSON output instructions.
    """
    return (
        "Classifica ogni descrizione transazione nella categoria più appropriata.\n\n"
        f"Categorie disponibili: {json.dumps(categories, ensure_ascii=False)}\n\n"
        f"Descrizioni da classificare: {json.dumps(descriptions, ensure_ascii=False)}\n\n"
        "Restituisci un array JSON con oggetti: {\"description\": \"...\", \"category\": \"...\"}"
    )


def _parse_categorization_response(raw_text: str) -> Optional[dict]:
    """Parse the AI Gateway's raw response text into a description-to-category mapping.

    Strips markdown formatting from the response, parses the JSON payload,
    and validates that each item contains both 'description' and 'category'
    fields. Returns None if parsing or validation fails.

    Args:
        raw_text: Raw text response from the AI Gateway, potentially containing
            markdown formatting around a JSON array.

    Returns:
        A dictionary mapping description strings to category name strings,
        or None if the response could not be parsed or contained no valid items.
    """
    try:
        # Remove any markdown code block wrappers from the AI response
        clean = strip_markdown(raw_text)
        parsed = json.loads(clean)
        if not isinstance(parsed, list):
            return None

        # Extract description-to-category pairs from each item in the JSON array
        mapping = {}
        for item in parsed:
            if isinstance(item, dict) and 'description' in item and 'category' in item:
                mapping[item['description']] = item['category']
        return mapping if mapping else None
    except (json.JSONDecodeError, TypeError):
        return None


def _keyword_categorize(user, descriptions: list[str]) -> dict:
    """Categorize descriptions using keyword-based rule matching as a fallback.

    Fetches all user-defined CategoryRules ordered by priority (highest first)
    and creation date (oldest first). For each description, checks if any
    rule's keyword appears in the description text (case-insensitive).
    The first matching rule determines the category.

    Args:
        user: The user whose rules should be applied.
        descriptions: List of transaction description strings to categorize.

    Returns:
        A dictionary mapping each description to a category name string
        (or None if no rule matched).
    """
    rules = list(
        CategoryRule.objects.filter(user=user)
        .select_related('category')
        .order_by('-priority', 'created_at')
    )
    mapping = {}
    for desc in descriptions:
        category_name = None
        # Check rules in priority order; first match wins
        for rule in rules:
            if rule.keyword.lower() in desc.lower():
                category_name = rule.category.name
                break
        mapping[desc] = category_name
    return mapping


def _get_cache_key(user, descriptions: list[str]) -> str:
    """Build a deterministic cache key from user, descriptions, and available categories.

    Generates a cache key that incorporates the user ID, the list of descriptions,
    and the currently available categories (both user and system). This ensures
    that cache hits only occur when the categorization context is identical,
    preventing stale results when categories are added or removed.

    Args:
        user: The user requesting categorization.
        descriptions: List of transaction description strings (typically a single item).

    Returns:
        A cache key string prefixed with 'ai_cat:' followed by an MD5 hash
        of the concatenated context.
    """
    # Include current category names in the key so cache invalidates when categories change
    cat_names = list(
        Category.objects.filter(
            Q(user=user) | Q(is_system=True)
        ).values_list('name', flat=True).order_by('name')
    )
    content = f"{user.id}:{sorted(descriptions)}:{cat_names}"
    h = hashlib.md5(content.encode('utf-8')).hexdigest()
    return f"ai_cat:{h}"


def batch_categorize(user, descriptions: list[str]) -> dict:
    """Categorize a batch of unique transaction descriptions using AI with caching.

    This is the main entry point for AI-powered categorization. It follows a
    multi-stage process to maximize accuracy and performance:

    1. Deduplicate the input descriptions while preserving order
    2. Check Django cache for previously categorized results
    3. Send uncached descriptions to the AI Gateway in configurable batches
    4. Cache all AI results with a 30-day TTL
    5. For any descriptions where AI returned no result, fall back to
       keyword-based rule matching

    Args:
        user: The user requesting categorization (used for category lookup and caching).
        descriptions: List of transaction description strings to categorize.
            May contain duplicates which will be deduplicated internally.

    Returns:
        A dictionary mapping each input description (including duplicates)
        to a category name string or None if no category could be determined.
    """
    if not descriptions:
        return {}

    # Remove duplicates while preserving insertion order for consistent processing
    seen = set()
    unique_descs = [d for d in descriptions if not (d in seen or seen.add(d))]

    # Fetch all available categories (user-owned + system) for the AI to choose from
    cat_names = list(
        Category.objects.filter(
            Q(user=user) | Q(is_system=True)
        ).values_list('name', flat=True).order_by('name')
    )

    # Check cache for each description to avoid redundant AI calls
    uncached = []
    cached_mapping = {}
    for desc in unique_descs:
        cache_key = _get_cache_key(user, [desc])
        cached = cache.get(cache_key)
        if cached is not None:
            cached_mapping[desc] = cached
        else:
            uncached.append(desc)

    # If all descriptions were cached, return immediately without calling the AI
    if not uncached:
        return {d: cached_mapping.get(d) for d in descriptions}

    # If AI categorization is disabled via settings, use keyword matching only
    if not AI_CATEGORIZATION_ENABLED:
        keyword_map = _keyword_categorize(user, uncached)
        cached_mapping.update(keyword_map)
        return {d: cached_mapping.get(d) for d in descriptions}

    # Call AI Gateway for uncached descriptions in configurable batch sizes
    ai_mapping = {}
    for i in range(0, len(uncached), AI_CATEGORIZATION_BATCH_SIZE):
        batch = uncached[i:i + AI_CATEGORIZATION_BATCH_SIZE]
        prompt = _build_categorization_prompt(batch, cat_names)
        raw_text = call_ai_gateway(
            _CATEGORIZATION_SYSTEM_PROMPT,
            prompt,
            timeout=AI_CATEGORIZATION_TIMEOUT,
        )
        if raw_text is not None:
            batch_mapping = _parse_categorization_response(raw_text)
            if batch_mapping:
                ai_mapping.update(batch_mapping)

    # Cache AI results and merge into the overall mapping
    for desc in uncached:
        cat = ai_mapping.get(desc)
        cache_key = _get_cache_key(user, [desc])
        cache.set(cache_key, cat, timeout=AI_CATEGORIZATION_CACHE_TTL)
        cached_mapping[desc] = cat

    # For descriptions where AI returned None, fall back to keyword matching
    missing = [d for d in uncached if cached_mapping.get(d) is None]
    if missing:
        keyword_map = _keyword_categorize(user, missing)
        cached_mapping.update(keyword_map)

    # Return results preserving the original input order (including duplicates)
    return {d: cached_mapping.get(d) for d in descriptions}
