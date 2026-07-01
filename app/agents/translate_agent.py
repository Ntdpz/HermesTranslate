"""Translate Agent: applies matched rules to the original text via string replace."""

import re


def translate(context_md: str) -> str:
    """Extract original text and rules from MD template, apply replacements."""
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
    """Extract target translation from rule like 'Translate X to Y'."""
    match = re.search(r"to\s+['\"]?(.+?)['\"]?$", rule_text)
    if match:
        return match.group(1)
    return ""
