"""Hermes Agent LLM client — calls hermes chat -q with skills.

Auto-detects whether Hermes Agent is installed. Falls back gracefully
when running in Docker (where hermes CLI is not available).
"""
import asyncio
import logging
import re
import shutil

logger = logging.getLogger(__name__)

_HERMES_AVAILABLE: bool | None = None


def hermes_available() -> bool:
    """Check if hermes CLI is installed and reachable."""
    global _HERMES_AVAILABLE
    if _HERMES_AVAILABLE is None:
        _HERMES_AVAILABLE = shutil.which("hermes") is not None
        if _HERMES_AVAILABLE:
            logger.info("Hermes Agent CLI detected — LLM agents enabled")
        else:
            logger.info("Hermes Agent CLI not found — using rule-based fallback")
    return _HERMES_AVAILABLE


async def ask_hermes(prompt: str, skill: str, timeout: int = 60) -> str:
    """Call Hermes Agent via CLI with a specific skill loaded.

    Returns the LLM response text, stripped of session metadata and code fences.
    Raises RuntimeError if hermes is not available or fails.
    """
    if not hermes_available():
        raise RuntimeError("Hermes Agent CLI not available")

    proc = await asyncio.create_subprocess_exec(
        "hermes", "chat", "-q", prompt,
        "-s", skill,
        "--quiet",
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    try:
        stdout, stderr = await asyncio.wait_for(
            proc.communicate(), timeout=timeout
        )
    except asyncio.TimeoutError:
        proc.kill()
        await proc.wait()
        raise RuntimeError(f"Hermes agent '{skill}' timed out after {timeout}s")

    if proc.returncode != 0:
        err = stderr.decode(errors="replace").strip()
        raise RuntimeError(
            f"Hermes agent '{skill}' failed (exit {proc.returncode}): {err}"
        )

    output = stdout.decode(errors="replace").strip()

    # Strip "session_id: ..." prefix line
    output = re.sub(r"^session_id:\s*\S+\s*\n?", "", output).strip()

    # Strip ``` code fences
    output = re.sub(r"^```\w*\n?", "", output)
    output = re.sub(r"\n?```$", "", output)

    return output.strip()
