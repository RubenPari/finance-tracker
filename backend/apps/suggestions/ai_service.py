from __future__ import annotations

import json

from django.conf import settings
from django.core.cache import cache
from openai import OpenAI

from apps.utils import strip_markdown

AI_GATEWAY_URL = getattr(
    settings, "AI_GATEWAY_URL", "https://gateway.ai.vercel.com/v1/chat/completions"
)
AI_GATEWAY_KEY = getattr(settings, "AI_GATEWAY_KEY", "")
AI_GATEWAY_MODEL = getattr(
    settings, "AI_GATEWAY_MODEL", "xai/grok-4.1-fast-non-reasoning"
)
AI_SUGGESTIONS_TIMEOUT = getattr(settings, "AI_SUGGESTIONS_TIMEOUT", 10)

# Derive base_url from the full endpoint URL (e.g. .../v1/chat/completions -> .../v1)
_GATEWAY_BASE_URL = AI_GATEWAY_URL
if _GATEWAY_BASE_URL.endswith("/chat/completions"):
    _GATEWAY_BASE_URL = _GATEWAY_BASE_URL[: -len("/chat/completions")]

_client: OpenAI | None = None


def _get_client() -> OpenAI | None:
    global _client
    if _client is None and AI_GATEWAY_KEY:
        _client = OpenAI(api_key=AI_GATEWAY_KEY, base_url=_GATEWAY_BASE_URL)
    return _client


def call_ai_gateway(system_prompt: str, user_prompt: str, timeout: int = 10):
    """
    Generic call to Vercel AI Gateway.
    Returns raw text response or None on failure.
    """
    if not AI_GATEWAY_KEY:
        return None

    client = _get_client()
    if client is None:
        return None

    try:
        completion = client.chat.completions.create(
            model=AI_GATEWAY_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.3,
            max_tokens=2000,
            extra_headers={"X-Vercel-AI-Gateway-Version": "1"},
            timeout=timeout,
        )
        return completion.choices[0].message.content
    except Exception:  # Catch OpenAIError, connection errors, etc.
        return None


# ====== SUGGESTIONS SPECIFIC ======

_SUGGESTIONS_SYSTEM_PROMPT = (
    "Sei un consulente finanziario esperto. Analizza i dati forniti e restituisci "
    "3-5 suggerimenti personalizzati in italiano in formato JSON rigoroso. "
    "Ogni suggerimento deve avere i campi: type, title, message. "
    "Puoi anche aggiungere campi opzionali: category, color, amount, change_pct, etc. "
    "I suggerimenti devono essere pratici, narrativi e basati sui dati reali forniti."
)


def _build_suggestions_prompt(context_data: dict) -> str:
    return (
        "Analizza il seguente profilo di spesa e fornisci suggerimenti personalizzati:\n\n"
        f"{json.dumps(context_data, indent=2, ensure_ascii=False)}\n\n"
        "Restituisci la risposta come array JSON di oggetti con campi: "
        "type, title, message (e facoltativi category, color, amount, etc.)."
    )


def _parse_suggestions_response(raw_text: str) -> list | None:
    try:
        clean = strip_markdown(raw_text)
        parsed = json.loads(clean)
        if isinstance(parsed, list) and all(
            "type" in s and "title" in s and "message" in s for s in parsed
        ):
            return parsed
        return None
    except (json.JSONDecodeError, TypeError):
        return None


def generate_suggestions(
    user, context_data: dict, force_refresh: bool = False
) -> list | None:
    """
    Genera suggerimenti via Vercel AI Gateway (xai/grok-4.1-fast-non-reasoning).
    Usa cache Django/Redis con TTL 24h, invalidata su nuovo import.
    Ritorna None se il servizio AI non è disponibile o la risposta è invalida.
    """
    cache_key = f"suggestions:{user.id}"
    if not force_refresh:
        cached = cache.get(cache_key)
        if cached is not None:
            return cached

    prompt = _build_suggestions_prompt(context_data)
    raw_text = call_ai_gateway(
        _SUGGESTIONS_SYSTEM_PROMPT, prompt, timeout=AI_SUGGESTIONS_TIMEOUT
    )
    if raw_text is None:
        return None

    suggestions = _parse_suggestions_response(raw_text)
    if suggestions:
        cache.set(cache_key, suggestions, timeout=86400)
        return suggestions
    return None


def invalidate_suggestions_cache(user):
    """Invalida la cache dei suggerimenti per l'utente (da chiamare dopo import)."""
    cache_key = f"suggestions:{user.id}"
    cache.delete(cache_key)
