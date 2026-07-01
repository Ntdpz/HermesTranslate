import pytest
from unittest.mock import patch

from app.agents.main_agent import build_context
from app.agents.translate_agent import translate
from app.agents.validate_agent import validate

@pytest.mark.asyncio
async def test_1_build_context_with_rules():
    mock_rules = [
        {"keyword": "Hello", "rule_text": "Translate Hello to สวัสดี", "updated_at": "2026-07-01"}
    ]
    with patch("app.agents.main_agent.extract_rules", return_value=mock_rules):
        ctx = await build_context("test-1", "Hello world")
        assert "Translation Task" in ctx
        assert "Original Text" in ctx
        assert "Matched Rules" in ctx
        assert "Instructions" in ctx
        assert "Translate Hello to สวัสดี" in ctx

@pytest.mark.asyncio
async def test_2_build_context_no_rules():
    with patch("app.agents.main_agent.extract_rules", return_value=[]):
        ctx = await build_context("test-2", "No keywords here")
        assert "no specific rules matched" in ctx

def test_3_translate_apply_rules():
    ctx = (
        "## Original Text\nHello world\n\n"
        "## Matched Rules\n"
        "1. **Hello**: Translate Hello to 'สวัสดี' (updated: 2026-07-01)\n"
    )
    result = translate(ctx)
    assert "Hello" not in result
    assert "สวัสดี" in result

def test_4_translate_empty_input():
    result = translate("")
    assert result == ""

@pytest.mark.asyncio
async def test_5_validate_pass():
    with patch("app.agents.validate_agent.extract_rules", return_value=[]):
        result = await validate("สวัสดี ชาวโลก")
        assert result is True

@pytest.mark.asyncio
async def test_6_validate_fail():
    mock_rules = [
        {"keyword": "Hello", "rule_text": "Translate Hello to สวัสดี", "updated_at": "2026-07-01"}
    ]
    with patch("app.agents.validate_agent.extract_rules", return_value=mock_rules):
        result = await validate("Hello world with AI")
        assert result is False
