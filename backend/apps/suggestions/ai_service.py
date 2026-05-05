import os
import json
import httpx
from typing import Optional
from django.conf import settings
from django.core.cache import cache
from django.utils import timezone

AI_GATEWAY_URL = getattr(settings, 'AI_GATEWAY_URL', 'https://gateway.ai.vercel.com/v1/chat/completions')
AI_GATEWAY_KEY = getattr(settings, 'AI_GATEWAY_KEY', '')
AI_GATEWAY_MODEL = getattr(settings, 'AI_GATEWAY_MODEL', 'gpt-5')
AI_SUGGESTIONS_TIMEOUT = getattr(settings, 'AI_SUGGESTIONS_TIMEOUT', 10)

SYSTEM_PROMPT = (
    "Sei un consulente finanziario esperto. Analizza i dati forniti e restituisci "
    "3-5 suggerimenti personalizzati in italiano in formato JSON rigoroso. "
    "Ogni suggerimento deve avere i campi: type, title, message. "
    "Puoi anche aggiungere campi opzionali: category, color, amount, change_pct, etc. "
    "I suggerimenti devono essere pratici, narrativi e basati sui dati reali forniti."
)


def _build_prompt(context_data: dict) -> str:
    prompt = (
        "Analizza il seguente profilo di spesa e fornisci suggerimenti personalizzati:\n\n"
        f"{json.dumps(context_data, indent=2, ensure_ascii=False)}\n\n"
        "Restituisci la risposta come array JSON di oggetti con campi: "
        "type, title, message (e facoltativi category, color, amount, etc.)."
    )
    return prompt


def _parse_ai_response(raw_text: str) -> Optional[list]:
    """Estrae e valida array JSON dalla risposta AI."""
    try:
        # Rimuovi eventuali backticks markdown
        clean = raw_text.strip()
        if clean.startswith('```json'):
            clean = clean[7:]
        if clean.startswith('```'):
            clean = clean[3:]
        if clean.endswith('```'):
            clean = clean[:-3]
        clean = clean.strip()

        parsed = json.loads(clean)
        if isinstance(parsed, list) and all('type' in s and 'title' in s and 'message' in s for s in parsed):
            return parsed
        return None
    except (json.JSONDecodeError, TypeError):
        return None


def generate_suggestions(user, context_data: dict, force_refresh: bool = False) -> Optional[list]:
    """
    Genera suggerimenti via Vercel AI Gateway (GPT-5).
    Usa cache Django/Redis con TTL 24h, invalidata su nuovo import.
    Ritorna None se il servizio AI non è disponibile o la risposta è invalida.
    """
    if not AI_GATEWAY_KEY:
        return None

    # Cache lookup
    cache_key = f'suggestions:{user.id}'
    if not force_refresh:
        cached = cache.get(cache_key)
        if cached is not None:
            return cached

    prompt = _build_prompt(context_data)
    try:
        with httpx.Client(timeout=AI_SUGGESTIONS_TIMEOUT) as client:
            response = client.post(
                AI_GATEWAY_URL,
                headers={
                    'Authorization': f'Bearer {AI_GATEWAY_KEY}',
                    'Content-Type': 'application/json',
                },
                json={
                    'model': AI_GATEWAY_MODEL,
                    'messages': [
                        {'role': 'system', 'content': SYSTEM_PROMPT},
                        {'role': 'user', 'content': prompt},
                    ],
                    'temperature': 0.7,
                    'max_tokens': 2000,
                },
            )
            response.raise_for_status()
            payload = response.json()
            raw_text = payload['choices'][0]['message']['content']
            suggestions = _parse_ai_response(raw_text)

            if suggestions:
                # Salva in cache per 24h = 86400 secondi
                cache.set(cache_key, suggestions, timeout=86400)
                return suggestions
            return None
    except (httpx.HTTPError, httpx.TimeoutException, KeyError, IndexError):
        return None


def invalidate_cache(user):
    """Invalida la cache dei suggerimenti per l'utente (da chiamare dopo import)."""
    cache_key = f'suggestions:{user.id}'
    cache.delete(cache_key)
