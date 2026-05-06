import json
import hashlib
from typing import Optional
from django.conf import settings
from django.core.cache import cache
from django.db.models import Q

from apps.suggestions.ai_service import call_ai_gateway
from apps.categories.models import Category, CategoryRule
from apps.utils import strip_markdown


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
        clean = strip_markdown(raw_text)
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

    seen = set()
    unique_descs = [d for d in descriptions if not (d in seen or seen.add(d))]

    cat_names = list(
        Category.objects.filter(
            Q(user=user) | Q(is_system=True)
        ).values_list('name', flat=True).order_by('name')
    )

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
        keyword_map = _keyword_categorize(user, uncached)
        cached_mapping.update(keyword_map)
        return {d: cached_mapping.get(d) for d in descriptions}

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

    for desc in uncached:
        cat = ai_mapping.get(desc)
        cache_key = _get_cache_key(user, [desc])
        cache.set(cache_key, cat, timeout=AI_CATEGORIZATION_CACHE_TTL)
        cached_mapping[desc] = cat

    missing = [d for d in uncached if cached_mapping.get(d) is None]
    if missing:
        keyword_map = _keyword_categorize(user, missing)
        cached_mapping.update(keyword_map)

    return {d: cached_mapping.get(d) for d in descriptions}
