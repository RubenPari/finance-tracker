import json
import hashlib
from typing import Optional
from django.conf import settings
from django.core.cache import cache

from apps.suggestions.ai_service import call_ai_gateway
from apps.categories.models import Category, CategoryRule


AI_CATEGORIZATION_ENABLED = getattr(settings, 'AI_CATEGORIZATION_ENABLED', True)
AI_CATEGORIZATION_BATCH_SIZE = getattr(settings, 'AI_CATEGORIZATION_BATCH_SIZE', 20)
AI_CATEGORIZATION_TIMEOUT = getattr(settings, 'AI_CATEGORIZATION_TIMEOUT', 15)
AI_CATEGORIZATION_CACHE_TTL = getattr(settings, 'AI_CATEGORIZATION_CACHE_TTL', 2592000)  # 30 days

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
    return (
        "Classifica ogni descrizione transazione nella categoria più appropriata.\n\n"
        f"Categorie disponibili: {json.dumps(categories, ensure_ascii=False)}\n\n"
        f"Descrizioni da classificare: {json.dumps(descriptions, ensure_ascii=False)}\n\n"
        "Restituisci un array JSON con oggetti: {\"description\": \"...\", \"category\": \"...\"}"
    )


def _parse_categorization_response(raw_text: str) -> Optional[dict]:
    """
    Parse AI response into dict {description: category_name}.
    Returns None if parsing fails.
    """
    try:
        clean = raw_text.strip()
        if clean.startswith('```json'):
            clean = clean[7:]
        if clean.startswith('```'):
            clean = clean[3:]
        if clean.endswith('```'):
            clean = clean[:-3]
        clean = clean.strip()

        parsed = json.loads(clean)
        if not isinstance(parsed, list):
            return None

        mapping = {}
        for item in parsed:
            if isinstance(item, dict) and 'description' in item and 'category' in item:
                mapping[item['description']] = item['category']
        return mapping if mapping else None
    except (json.JSONDecodeError, TypeError):
        return None


def _keyword_categorize(user, descriptions: list[str]) -> dict:
    """
    Fallback: classify using existing CategoryRule keyword matching.
    Returns {description: category_name}.
    """
    rules = list(
        CategoryRule.objects.filter(user=user)
        .select_related('category')
        .order_by('-priority', 'created_at')
    )
    mapping = {}
    for desc in descriptions:
        category_name = None
        for rule in rules:
            if rule.keyword.lower() in desc.lower():
                category_name = rule.category.name
                break
        mapping[desc] = category_name
    return mapping


def _get_cache_key(user, descriptions: list[str]) -> str:
    """Build deterministic cache key from user + descriptions + available categories."""
    cat_names = list(
        Category.objects.filter(
            models_q(user=user) | models_q(is_system=True)
        ).values_list('name', flat=True).order_by('name')
    )
    # Use MD5 hash for fixed-length key
    content = f"{user.id}:{sorted(descriptions)}:{cat_names}"
    h = hashlib.md5(content.encode('utf-8')).hexdigest()
    return f"ai_cat:{h}"


def batch_categorize(user, descriptions: list[str]) -> dict:
    """
    Categorize a batch of unique descriptions using AI Gateway.
    Returns {description: category_name_or_None}.
    
    Flow:
    1. Check cache per description
    2. Call AI Gateway in batch for uncached descriptions
    3. Cache results
    4. If AI fails, fallback to keyword matching
    """
    if not descriptions:
        return {}

    # Deduplicate while preserving order
    seen = set()
    unique_descs = [d for d in descriptions if not (d in seen or seen.add(d))]

    # Get available categories for user
    from django.db.models import Q as models_q
    global models_q
    cat_names = list(
        Category.objects.filter(
            models_q(user=user) | models_q(is_system=True)
        ).values_list('name', flat=True).order_by('name')
    )

    # Check cache for each description
    uncached = []
    cached_mapping = {}
    for desc in unique_descs:
        cache_key = _get_cache_key(user, [desc])
        cached = cache.get(cache_key)
        if cached is not None:
            cached_mapping[desc] = cached
        else:
            uncached.append(desc)

    if not uncached:
        return {d: cached_mapping.get(d) for d in descriptions}

    if not AI_CATEGORIZATION_ENABLED:
        # AI disabled, use keyword fallback
        keyword_map = _keyword_categorize(user, uncached)
        cached_mapping.update(keyword_map)
        return {d: cached_mapping.get(d) for d in descriptions}

    # Batch AI calls (max AI_CATEGORIZATION_BATCH_SIZE at a time)
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

    # Cache AI results (and None for missed descriptions)
    for desc in uncached:
        cat = ai_mapping.get(desc)
        cache_key = _get_cache_key(user, [desc])
        cache.set(cache_key, cat, timeout=AI_CATEGORIZATION_CACHE_TTL)
        cached_mapping[desc] = cat

    # If any description failed AI, fill gaps with keyword fallback
    missing = [d for d in uncached if cached_mapping.get(d) is None]
    if missing:
        keyword_map = _keyword_categorize(user, missing)
        cached_mapping.update(keyword_map)

    return {d: cached_mapping.get(d) for d in descriptions}


import json
import hashlib
from typing import Optional
from django.conf import settings
from django.core.cache import cache
from django.db.models import Q

from apps.suggestions.ai_service import call_ai_gateway
from apps.categories.models import Category, CategoryRule


AI_CATEGORIZATION_ENABLED = getattr(settings, 'AI_CATEGORIZATION_ENABLED', True)
AI_CATEGORIZATION_BATCH_SIZE = getattr(settings, 'AI_CATEGORIZATION_BATCH_SIZE', 20)
AI_CATEGORIZATION_TIMEOUT = getattr(settings, 'AI_CATEGORIZATION_TIMEOUT', 15)
AI_CATEGORIZATION_CACHE_TTL = getattr(settings, 'AI_CATEGORIZATION_CACHE_TTL', 2592000)  # 30 days

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
    return (
        "Classifica ogni descrizione transazione nella categoria più appropriata.\n\n"
        f"Categorie disponibili: {json.dumps(categories, ensure_ascii=False)}\n\n"
        f"Descrizioni da classificare: {json.dumps(descriptions, ensure_ascii=False)}\n\n"
        "Restituisci un array JSON con oggetti: {\"description\": \"...\", \"category\": \"...\"}"
    )


def _parse_categorization_response(raw_text: str) -> Optional[dict]:
    """
    Parse AI response into dict {description: category_name}.
    Returns None if parsing fails.
    """
    try:
        clean = raw_text.strip()
        if clean.startswith('```json'):
            clean = clean[7:]
        if clean.startswith('```'):
            clean = clean[3:]
        if clean.endswith('```'):
            clean = clean[:-3]
        clean = clean.strip()

        parsed = json.loads(clean)
        if not isinstance(parsed, list):
            return None

        mapping = {}
        for item in parsed:
            if isinstance(item, dict) and 'description' in item and 'category' in item:
                mapping[item['description']] = item['category']
        return mapping if mapping else None
    except (json.JSONDecodeError, TypeError):
        return None


def _keyword_categorize(user, descriptions: list[str]) -> dict:
    """
    Fallback: classify using existing CategoryRule keyword matching.
    Returns {description: category_name}.
    """
    rules = list(
        CategoryRule.objects.filter(user=user)
        .select_related('category')
        .order_by('-priority', 'created_at')
    )
    mapping = {}
    for desc in descriptions:
        category_name = None
        for rule in rules:
            if rule.keyword.lower() in desc.lower():
                category_name = rule.category.name
                break
        mapping[desc] = category_name
    return mapping


def _get_cache_key(user, descriptions: list[str]) -> str:
    """Build deterministic cache key from user + descriptions + available categories."""
    cat_names = list(
        Category.objects.filter(
            Q(user=user) | Q(is_system=True)
        ).values_list('name', flat=True).order_by('name')
    )
    # Use MD5 hash for fixed-length key
    content = f"{user.id}:{sorted(descriptions)}:{cat_names}"
    h = hashlib.md5(content.encode('utf-8')).hexdigest()
    return f"ai_cat:{h}"


def _cache_category_result(user, desc: str, category_name: str):
    cache_key = _get_cache_key(user, [desc])
    cache.set(cache_key, category_name, timeout=AI_CATEGORIZATION_CACHE_TTL)


def _cache_and_return(user, descriptions: list[str], mapping: dict) -> dict:
    for desc in descriptions:
        _cache_category_result(user, desc, mapping.get(desc))
    return {d: mapping.get(d) for d in descriptions}


def batch_categorize(user, descriptions: list[str]) -> dict:
    """
    Categorize a batch of unique descriptions using AI Gateway.
    Returns {description: category_name_or_None}.

    Flow:
    1. Check cache per description
    2. Call AI Gateway in batch for uncached descriptions
    3. Cache results
    4. If AI fails, fallback to keyword matching
    """
    if not descriptions:
        return {}

    # Deduplicate while preserving order
    seen = set()
    unique_descs = [d for d in descriptions if not (d in seen or seen.add(d))]

    # Get available categories for user
    cat_names = list(
        Category.objects.filter(
            Q(user=user) | Q(is_system=True)
        ).values_list('name', flat=True).order_by('name')
    )

    # Check cache for each description
    uncached = []
    cached_mapping = {}
    for desc in unique_descs:
        cache_key = _get_cache_key(user, [desc])
        cached = cache.get(cache_key)
        if cached is not None:  # could be cached None as well
            cached_mapping[desc] = cached
        else:
            uncached.append(desc)

    if not uncached:
        return {d: cached_mapping.get(d) for d in descriptions}

    if not AI_CATEGORIZATION_ENABLED:
        keyword_map = _keyword_categorize(user, uncached)
        cached_mapping.update(keyword_map)
        for desc in uncached:
            _cache_category_result(user, desc, keyword_map.get(desc))
        return {d: cached_mapping.get(d) for d in descriptions}

    # Batch AI calls (max AI_CATEGORIZATION_BATCH_SIZE at a time)
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

    # Cache AI results (and None for missed descriptions)
    for desc in uncached:
        cat = ai_mapping.get(desc)
        cache_key = _get_cache_key(user, [desc])
        cache.set(cache_key, cat, timeout=AI_CATEGORIZATION_CACHE_TTL)
        cached_mapping[desc] = cat

    # If any description failed AI, fill gaps with keyword fallback
    missing = [d for d in uncached if cached_mapping.get(d) is None]
    if missing:
        keyword_map = _keyword_categorize(user, missing)
        for desc in missing:
            if keyword_map.get(desc):
                cached_mapping[desc] = keyword_map[desc]
                _cache_category_result(user, desc, keyword_map[desc])

    return {d: cached_mapping.get(d) for d in descriptions}
