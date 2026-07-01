import asyncio

import ahocorasick
from sqlalchemy import select

from app.db.database import async_session_factory
from app.db.models import TranslationRule

_automaton = None
_lock = asyncio.Lock()


async def _load_rules():
    async with async_session_factory() as session:
        result = await session.execute(
            select(TranslationRule).order_by(TranslationRule.updated_at.desc())
        )
        rules = []
        seen_keywords = set()
        for r in result.scalars().all():
            if r.keyword not in seen_keywords:
                seen_keywords.add(r.keyword)
                rules.append((r.keyword, r.rule_text, r.updated_at, str(r.id)))
        return rules


def _build_automaton(rules):
    a = ahocorasick.Automaton()
    for keyword, rule_text, updated_at, rule_id in rules:
        a.add_word(keyword, (keyword, rule_text, updated_at, rule_id))
    if rules:
        a.make_automaton()
    return a


async def reload():
    global _automaton
    rules = await _load_rules()
    async with _lock:
        _automaton = _build_automaton(rules)


async def _get_automaton():
    global _automaton
    if _automaton is None:
        await reload()
    return _automaton


async def extract_rules(text: str) -> list[dict]:
    automaton = await _get_automaton()
    matches = []
    seen = set()
    try:
        for _end, (keyword, rule_text, updated_at, rule_id) in automaton.iter(text):
            if rule_id not in seen:
                seen.add(rule_id)
                matches.append(
                    {
                        "keyword": keyword,
                        "rule_text": rule_text,
                        "rule_id": rule_id,
                        "updated_at": updated_at.isoformat(),
                    }
                )
    except AttributeError:
        pass  # empty automaton with no rules loaded
    matches.sort(key=lambda m: m["updated_at"], reverse=True)
    return matches


_bg_task = None


async def _bg_refresh(interval: int):
    while True:
        try:
            await reload()
        except Exception:
            pass
        await asyncio.sleep(interval)


async def start_bg_refresh(interval: int = 60):
    global _bg_task
    if _bg_task is None:
        _bg_task = asyncio.create_task(_bg_refresh(interval))


async def stop_bg_refresh():
    global _bg_task
    if _bg_task:
        _bg_task.cancel()
        try:
            await _bg_task
        except asyncio.CancelledError:
            pass
        _bg_task = None
