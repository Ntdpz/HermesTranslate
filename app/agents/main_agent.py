"""Main Agent: uses Hermes Agent (LLM) with rule-based fallback."""
import logging

from app.llm import ask_hermes, hermes_available
from app.services.rule_engine import extract_rules

logger = logging.getLogger(__name__)


async def build_context(task_id: str, text: str) -> str:
    rules = await extract_rules(text)

    if hermes_available():
        try:
            return await _build_context_llm(text, rules)
        except Exception as e:
            logger.warning("Hermes main agent failed, falling back: %s", e)

    return _build_context_rule_based(text, rules)


async def _build_context_llm(text: str, rules: list) -> str:
    if rules:
        rules_text = "\n".join(
            f"{i}. **{r['keyword']}**: {r['rule_text']} (updated: {r['updated_at']})"
            for i, r in enumerate(rules, 1)
        )
    else:
        rules_text = "(no specific rules matched)"

    prompt = f"""Original text: {text}
Matched rules:
{rules_text}

Build the translation context."""
    return await ask_hermes(prompt, "translate-main")


def _build_context_rule_based(text: str, rules: list) -> str:
    if rules:
        rules_section = "\n## Matched Rules\n"
        for i, r in enumerate(rules, 1):
            rules_section += (
                f"{i}. **{r['keyword']}**: {r['rule_text']} "
                f"(updated: {r['updated_at']})\n"
            )
    else:
        rules_section = "\n## Matched Rules\n(no specific rules matched)\n"

    return (
        f"# Translation Task\n"
        f"**Task ID**: `console`\n\n"
        f"## Original Text\n{text}\n\n"
        f"{rules_section}\n"
        f"## Instructions\n"
        f"Translate the original text following the matched rules above. "
        f"Preserve the original meaning while applying all applicable rules.\n"
    )
