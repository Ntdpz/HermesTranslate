"""Translate Agent: uses Hermes Agent (LLM) with regex fallback."""
import logging
import re

from app.llm import ask_hermes, hermes_available

logger = logging.getLogger(__name__)


async def translate(context_md: str) -> str:
    if hermes_available():
        try:
            return await _translate_llm(context_md)
        except Exception as e:
            logger.warning("Hermes translate agent failed, falling back: %s", e)

    return _translate_rule_based(context_md)


async def _translate_llm(context_md: str) -> str:
    prompt = f"""Translate this text following the rules:

{context_md}

Translate to English."""
    return await ask_hermes(prompt, "translate-worker")


def _translate_rule_based(context_md: str) -> str:
    original_match = re.search(r"## Original Text\n(.+?)\n\n", context_md, re.DOTALL)
    if not original_match:
        return ""
    text = original_match.group(1)

    rule_pattern = re.findall(
        r"\d+\. \*\*(.+?)\*\*: (.+?) \(updated:", context_md
    )
    for keyword, rule_text in rule_pattern:
        replacement = _extract_replacement(rule_text)
        if replacement:
            text = text.replace(keyword, replacement)

    return text


def _extract_replacement(rule_text: str) -> str:
    match = re.search(r"to\s+['\"]?(.+?)['\"]?$", rule_text)
    if match:
        return match.group(1)
    return ""
