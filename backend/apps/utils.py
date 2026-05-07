"""Shared utility functions used across the backend application.

Currently provides a single helper to strip markdown code fences
from AI-generated responses so that raw JSON can be parsed.
"""


def strip_markdown(text: str) -> str:
    """Strip markdown code fences from AI response text.

    AI models often wrap JSON payloads in triple-backtick code fences
    (e.g., ```json ... ```). This function removes those fences so
    the remaining text can be parsed as raw JSON.

    Args:
        text: The raw text response from an AI model, potentially
            containing markdown code fences.

    Returns:
        The cleaned text with code fences removed and whitespace trimmed.
    """
    clean = text.strip()
    if clean.startswith('```json'):
        clean = clean[7:]
    if clean.startswith('```'):
        clean = clean[3:]
    if clean.endswith('```'):
        clean = clean[:-3]
    return clean.strip()
