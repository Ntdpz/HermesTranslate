"""Validate Agent: checks translated text against rules using Aho-Corasick."""

from app.services.rule_engine import extract_rules


async def validate(translated_text: str) -> bool:
    """Return True if NO remaining keyword violations exist."""
    remaining = await extract_rules(translated_text)
    return len(remaining) == 0
