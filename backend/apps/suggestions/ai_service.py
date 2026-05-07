"""AI service for generating personalized transaction suggestions.

This module integrates with the Vercel AI Gateway to produce financial insights
based on aggregated user spending data. It provides caching to reduce API calls
and gracefully falls back when the AI service is unavailable. The service uses
the OpenAI Python client library to communicate with the gateway endpoint.
"""

from __future__ import annotations

import json

from django.conf import settings
from django.core.cache import cache
from openai import OpenAI

from apps.utils import strip_markdown

# Configuration constants loaded from Django settings with sensible defaults.
# These control the AI gateway endpoint, authentication, model selection, and timeout.
AI_GATEWAY_URL = getattr(
    settings, "AI_GATEWAY_URL", "https://ai-gateway.vercel.sh/v1/chat/completions"
)
AI_GATEWAY_KEY = getattr(settings, "AI_GATEWAY_KEY", "")
AI_GATEWAY_MODEL = getattr(
    settings, "AI_GATEWAY_MODEL", "xai/grok-4.1-fast-non-reasoning"
)
AI_SUGGESTIONS_TIMEOUT = getattr(settings, "AI_SUGGESTIONS_TIMEOUT", 10)

# Derive base_url from the full endpoint URL (e.g. .../v1/chat/completions -> .../v1)
# The OpenAI client expects the base URL without the /chat/completions suffix.
_GATEWAY_BASE_URL = AI_GATEWAY_URL
if _GATEWAY_BASE_URL.endswith("/chat/completions"):
    _GATEWAY_BASE_URL = _GATEWAY_BASE_URL[: -len("/chat/completions")]

# Module-level singleton for the OpenAI client, lazily initialized
_client: OpenAI | None = None


def _get_client() -> OpenAI | None:
    """Lazily initialize and return the OpenAI client singleton.

    The client is created only once on first call and reused for subsequent
    invocations. If no API key is configured, returns None.

    Returns:
        OpenAI | None: The initialized OpenAI client instance, or None if
            the API key is not configured.
    """
    global _client
    if _client is None and AI_GATEWAY_KEY:
        _client = OpenAI(api_key=AI_GATEWAY_KEY, base_url=_GATEWAY_BASE_URL)
    return _client


def call_ai_gateway(system_prompt: str, user_prompt: str, timeout: int = 10):
    """Make a generic completion request to the Vercel AI Gateway.

    Sends a chat completion request with system and user prompts to the
    configured AI gateway endpoint. This is a low-level function used by
    higher-level suggestion generation routines.

    Args:
        system_prompt: The system message that sets the AI's behavior context.
        user_prompt: The user message containing the data to be analyzed.
        timeout: Maximum seconds to wait for a response (default: 10).

    Returns:
        str | None: The raw text response from the AI, or None if the API key
            is missing, the client is unavailable, or an exception occurs.
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
            # Low temperature for more consistent, deterministic responses
            temperature=0.3,
            # Limit response length to control costs and parsing reliability
            max_tokens=2000,
            # Required header for Vercel AI Gateway v1 protocol
            extra_headers={"X-Vercel-AI-Gateway-Version": "1"},
            timeout=timeout,
        )
        return completion.choices[0].message.content
    except Exception:  # Catch OpenAIError, connection errors, etc.
        return None


# ====== SUGGESTIONS SPECIFIC ======

# System prompt that defines the AI's role as an expert financial advisor.
# It instructs the model to return 3-5 personalized suggestions in Italian,
# formatted as strict JSON with required fields (type, title, message) and
# optional fields (category, color, amount, change_pct, etc.).
_SUGGESTIONS_SYSTEM_PROMPT = (
    "You are an expert financial advisor. Analyze the provided data and return "
    "3-5 personalized suggestions in Italian in strict JSON format. "
    "Each suggestion must have the fields: type, title, message. "
    "You may also add optional fields: category, color, amount, change_pct, etc. "
    "Suggestions must be practical, narrative-driven, and based on the actual data provided."
)


def _build_suggestions_prompt(context_data: dict) -> str:
    """Build the user prompt for the AI suggestion request.

    Serializes the aggregated spending context dictionary into a formatted
    JSON string and wraps it with instructions for the AI to analyze and
    return personalized financial suggestions.

    Args:
        context_data: A dictionary containing aggregated spending data
            (trends, categories, changes, subscriptions, outliers) as built
            by _build_ai_context in views.py.

    Returns:
        str: The formatted user prompt string containing the JSON context
            and instructions for generating suggestions.
    """
    return (
        "Analyze the following spending profile and provide personalized suggestions:\n\n"
        f"{json.dumps(context_data, indent=2, ensure_ascii=False)}\n\n"
        "Return the response as a JSON array of objects with fields: "
        "type, title, message (and optional category, color, amount, etc.)."
    )


def _parse_suggestions_response(raw_text: str) -> list | None:
    """Parse and validate the AI's raw text response into a structured list.

    Strips any markdown formatting from the response, attempts to parse it as
    JSON, and validates that the result is a list of dictionaries containing
    the required fields (type, title, message).

    Args:
        raw_text: The raw text response from the AI gateway.

    Returns:
        list | None: A list of validated suggestion dictionaries, or None if
            the response cannot be parsed or fails validation.
    """
    try:
        # Remove markdown code block fences if present
        clean = strip_markdown(raw_text)
        parsed = json.loads(clean)
        # Validate that the response is a non-empty list where each suggestion
        # has the required minimum fields
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
    """Generate AI-powered financial suggestions via the Vercel AI Gateway.

    Uses Django's caching framework (Redis-backed) with a 24-hour TTL to avoid
    redundant API calls. The cache is automatically invalidated when new
    transactions are imported. If the AI service is unavailable or returns
    invalid data, this function returns None, signaling the caller to fall
    back to the legacy statistical analysis.

    Args:
        user: The Django user to generate suggestions for.
        context_data: Aggregated spending context dictionary produced by
            _build_ai_context in views.py.
        force_refresh: If True, bypass the cache and always call the AI gateway.

    Returns:
        list | None: A list of suggestion dictionaries on success, or None if
            the AI service is unavailable, the response is invalid, or the
            API key is not configured.
    """
    # Cache key is user-specific to prevent suggestion leakage between users
    cache_key = f"suggestions:{user.id}"
    if not force_refresh:
        cached = cache.get(cache_key)
        if cached is not None:
            return cached

    # Build the prompt from the user's spending context and call the AI gateway
    prompt = _build_suggestions_prompt(context_data)
    raw_text = call_ai_gateway(
        _SUGGESTIONS_SYSTEM_PROMPT, prompt, timeout=AI_SUGGESTIONS_TIMEOUT
    )
    if raw_text is None:
        return None

    # Parse and validate the AI response before caching
    suggestions = _parse_suggestions_response(raw_text)
    if suggestions:
        # Cache for 24 hours (86400 seconds)
        cache.set(cache_key, suggestions, timeout=86400)
        return suggestions
    return None


def invalidate_suggestions_cache(user):
    """Invalidate the cached suggestions for a specific user.

    This should be called after new transactions are imported to ensure
    the next suggestion request generates fresh insights based on the
    updated data.

    Args:
        user: The Django user whose cached suggestions should be cleared.
    """
    cache_key = f"suggestions:{user.id}"
    cache.delete(cache_key)
