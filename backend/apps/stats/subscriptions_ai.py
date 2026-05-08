"""AI-powered classification for recurring subscription candidates.

This module is used by the stats subscriptions endpoint to reduce false positives
and recover missed subscriptions by classifying clustered transaction patterns.
"""

from __future__ import annotations

import json
import hashlib
from typing import Any

from django.core.cache import cache

from apps.utils import strip_markdown
from apps.suggestions.ai_service import call_ai_gateway


_SYSTEM_PROMPT = (
    "Sei un assistente che classifica cluster di transazioni come abbonamenti oppure no. "
    "Un abbonamento puo' avere cadenza regolare (settimanale/mensile/trimestrale/annuale) "
    "oppure essere irregolare ma ripetuto (es. servizi a consumo ricaricati spesso). "
    "Devi essere prudente con falsi positivi come ristoranti, supermercati, shopping casuale. "
    "Rispondi SOLO con JSON valido, senza markdown.\n\n"
    "Schema output (array):\n"
    "[\n"
    "  {\n"
    '    \"cluster_key\": \"<string>\",\n'
    '    \"is_subscription\": <true|false>,\n'
    '    \"confidence\": <number 0..1>,\n'
    '    \"frequency\": \"weekly|monthly|quarterly|yearly|irregular\",\n'
    '    \"canonical_merchant\": \"<string>\",\n'
    '    \"reason\": \"<short italian reason>\"\n'
    "  }\n"
    "]\n"
)


def _cache_key(user_id: int, payload_hash: str) -> str:
    return f"stats:subscriptions_ai:{user_id}:{payload_hash}"


def _hash_payload(payload: dict[str, Any]) -> str:
    raw = json.dumps(payload, ensure_ascii=False, sort_keys=True).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def _parse_ai_response(raw_text: str) -> list[dict[str, Any]] | None:
    try:
        clean = strip_markdown(raw_text)
        parsed = json.loads(clean)
        if not isinstance(parsed, list):
            return None
        out: list[dict[str, Any]] = []
        for item in parsed:
            if not isinstance(item, dict):
                continue
            if "cluster_key" not in item or "is_subscription" not in item:
                continue
            out.append(item)
        return out if out else None
    except Exception:
        return None


def classify_subscription_candidates(
    *,
    user_id: int,
    candidates: list[dict[str, Any]],
    timeout: int = 12,
    cache_ttl_seconds: int = 86400,
) -> dict[str, dict[str, Any]]:
    """Classify candidate clusters with the AI gateway.

    Args:
        user_id: authenticated user id (used for cache partitioning).
        candidates: list of dicts with required keys:
            - cluster_key: deterministic key used by UI and overrides
            - merchant_examples: list[str]
            - charges: list[{date, amount, category?}]
            - stats: dict with precomputed fields (pattern_score, occurrences, etc.)

    Returns:
        dict mapping cluster_key -> ai_result dict with fields:
            is_subscription, confidence, frequency, canonical_merchant, reason
    """
    if not candidates:
        return {}

    payload = {"candidates": candidates}
    payload_hash = _hash_payload(payload)
    key = _cache_key(user_id, payload_hash)
    cached = cache.get(key)
    if isinstance(cached, dict):
        return cached

    user_prompt = (
        "Classifica questi cluster:\n\n"
        f"{json.dumps(payload, ensure_ascii=False, indent=2)}\n\n"
        "Regole: usa `cluster_key` per riferirti al cluster. "
        "Non inventare addebiti o date. "
        "Se non sei sicuro, metti is_subscription=false e confidence bassa.\n"
    )

    raw = call_ai_gateway(_SYSTEM_PROMPT, user_prompt, timeout=timeout)
    if not raw:
        return {}

    parsed = _parse_ai_response(raw)
    if not parsed:
        return {}

    result: dict[str, dict[str, Any]] = {}
    for item in parsed:
        ck = str(item.get("cluster_key", "")).strip()
        if not ck:
            continue
        result[ck] = {
            "is_subscription": bool(item.get("is_subscription")),
            "confidence": float(item.get("confidence", 0.0) or 0.0),
            "frequency": str(item.get("frequency", "irregular") or "irregular"),
            "canonical_merchant": str(item.get("canonical_merchant", "") or "").strip() or None,
            "reason": str(item.get("reason", "") or "").strip() or None,
        }

    cache.set(key, result, timeout=cache_ttl_seconds)
    return result

