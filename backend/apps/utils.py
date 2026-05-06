def strip_markdown(text: str) -> str:
    """Strip markdown code fences from AI response text."""
    clean = text.strip()
    if clean.startswith('```json'):
        clean = clean[7:]
    if clean.startswith('```'):
        clean = clean[3:]
    if clean.endswith('```'):
        clean = clean[:-3]
    return clean.strip()
