"""Validate Agent: uses Aho-Corasick + optional Hermes Agent (LLM) review."""
import logging

from app.llm import ask_hermes, hermes_available
from app.services.rule_engine import extract_rules

logger = logging.getLogger(__name__)


async def validate(translated_text: str) -> bool:
    """Return True if NO remaining keyword violations exist."""
    violations = await extract_rules(translated_text)

    if not violations:
        # No mechanical violations — optionally get LLM quality review
        if hermes_available():
            try:
                result = await ask_hermes(
                    f"Translated text: {translated_text}\nViolations found: (none)\nValidate.",
                    "translate-checker",
                )
                return result.strip().upper().startswith("PASS")
            except Exception as e:
                logger.warning("Hermes validate agent failed: %s", e)
        return True

    # Violations found — fail regardless of LLM
    return False
