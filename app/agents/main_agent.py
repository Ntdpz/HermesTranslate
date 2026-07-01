"""Main Agent: scans text with Aho-Corasick, builds MD template context."""

from app.services.rule_engine import extract_rules


async def build_context(task_id: str, text: str) -> str:
    rules = await extract_rules(text)
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
        f"**Task ID**: `{task_id}`\n\n"
        f"## Original Text\n{text}\n\n"
        f"{rules_section}\n"
        f"## Instructions\n"
        f"Translate the original text following the matched rules above. "
        f"Preserve the original meaning while applying all applicable rules.\n"
    )
