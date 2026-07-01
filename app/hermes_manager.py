"""Hermes Agent Dashboard Manager — process lifecycle + config for 3 profiles.

Manages 3 Hermes Agent profiles (ht-main, ht-translate, ht-validate) as
independent dashboard processes with start/stop/status control.  Also
provides config read/write, skill listing, and direct chat access.
"""
import asyncio
import json
import logging
import os
import re
import shutil
from pathlib import Path
from typing import Optional

import yaml
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/hermes", tags=["hermes-manager"])

# ---------------------------------------------------------------------------
# Agent definitions
# ---------------------------------------------------------------------------
AGENTS: dict[str, dict] = {
    "main":      {"profile": "ht-main",      "port": 9120, "skill": "translate-main"},
    "translate": {"profile": "ht-translate", "port": 9121, "skill": "translate-worker"},
    "validate":  {"profile": "ht-validate",  "port": 9122, "skill": "translate-checker"},
}

_processes: dict[str, asyncio.subprocess.Process] = {}

HERMES_HOME = Path(os.environ.get("HERMES_HOME", Path.home() / ".hermes"))

KNOWN_MODELS = [
    "deepseek/deepseek-chat",
    "deepseek/deepseek-reasoner",
    "deepseek-v4-pro",
    "anthropic/claude-sonnet-4",
    "anthropic/claude-opus-4",
    "openai/gpt-4o",
    "openai/o3-mini",
    "google/gemini-2.5-pro",
    "google/gemini-2.5-flash",
]


def _profile_dir(agent: str) -> Path:
    return HERMES_HOME / "profiles" / AGENTS[agent]["profile"]


def _has_hermes() -> bool:
    return shutil.which("hermes") is not None


# ---------------------------------------------------------------------------
# Pydantic models
# ---------------------------------------------------------------------------
class ConfigUpdate(BaseModel):
    model: Optional[str] = None
    provider: Optional[str] = None


class ChatRequest(BaseModel):
    text: str


class SkillInstallRequest(BaseModel):
    skill_id: str


# ---------------------------------------------------------------------------
# Dashboard lifecycle
# ---------------------------------------------------------------------------

@router.get("/dashboard/status")
async def dashboard_status():
    """Return status of all 3 Hermes dashboards."""
    result = {}
    for agent, cfg in AGENTS.items():
        proc = _processes.get(agent)
        if proc is not None and proc.returncode is None:
            result[agent] = {"running": True, "port": cfg["port"], "pid": proc.pid}
        else:
            result[agent] = {"running": False, "port": cfg["port"], "pid": None}
    return {"agents": result}


@router.post("/dashboard/start/{agent}")
async def dashboard_start(agent: str):
    """Start a Hermes dashboard for the given agent profile."""
    if agent not in AGENTS:
        raise HTTPException(400, f"Unknown agent: {agent}")
    if not _has_hermes():
        raise HTTPException(503, "Hermes CLI not found on this system")

    existing = _processes.get(agent)
    if existing is not None and existing.returncode is None:
        return {
            "agent": agent,
            "running": True,
            "port": AGENTS[agent]["port"],
            "pid": existing.pid,
            "message": "Already running",
        }

    cfg = AGENTS[agent]
    proc = await asyncio.create_subprocess_exec(
        "hermes", "-p", cfg["profile"],
        "dashboard",
        "--port", str(cfg["port"]),
        "--no-open",
        "--isolated",
        "--skip-build",
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    _processes[agent] = proc

    # Brief wait to catch immediate crashes
    await asyncio.sleep(2)
    if proc.returncode is not None:
        stderr_raw = b""
        if proc.stderr:
            stderr_raw = await proc.stderr.read()
        stderr_text = stderr_raw.decode(errors="replace")
        del _processes[agent]
        raise HTTPException(
            500,
            detail=f"Dashboard failed to start (exit {proc.returncode}): {stderr_text[:500]}",
        )

    logger.info("Dashboard started: %s on port %d (pid %d)", agent, cfg["port"], proc.pid)
    return {"agent": agent, "running": True, "port": cfg["port"], "pid": proc.pid}


@router.post("/dashboard/stop/{agent}")
async def dashboard_stop(agent: str):
    """Stop a running Hermes dashboard."""
    if agent not in AGENTS:
        raise HTTPException(400, f"Unknown agent: {agent}")

    proc = _processes.pop(agent, None)
    if proc is None or proc.returncode is not None:
        # Also try `hermes dashboard --stop` to clean up stale processes
        return {"agent": agent, "running": False, "message": "Was not running"}

    proc.terminate()
    try:
        await asyncio.wait_for(proc.wait(), timeout=5)
    except asyncio.TimeoutError:
        proc.kill()
        await proc.wait()

    logger.info("Dashboard stopped: %s", agent)
    return {"agent": agent, "running": False}


@router.post("/dashboard/open/{agent}")
async def dashboard_open(agent: str):
    """Return the URL to open a dashboard in browser."""
    if agent not in AGENTS:
        raise HTTPException(400, f"Unknown agent: {agent}")
    cfg = AGENTS[agent]
    return {"agent": agent, "url": f"http://127.0.0.1:{cfg['port']}"}


# ---------------------------------------------------------------------------
# Config management
# ---------------------------------------------------------------------------

@router.get("/config/{agent}")
async def config_get(agent: str):
    """Read the config.yaml for a given agent profile."""
    if agent not in AGENTS:
        raise HTTPException(400, f"Unknown agent: {agent}")

    config_path = _profile_dir(agent) / "config.yaml"
    if not config_path.exists():
        raise HTTPException(404, f"Config not found for agent '{agent}'")

    raw = config_path.read_text(encoding="utf-8")
    config = yaml.safe_load(raw) or {}

    model = config.get("model", {})
    return {
        "agent": agent,
        "model": model.get("default", ""),
        "provider": model.get("provider", ""),
    }


@router.post("/config/{agent}")
async def config_set(agent: str, update: ConfigUpdate):
    """Update model and/or provider for a given agent profile."""
    if agent not in AGENTS:
        raise HTTPException(400, f"Unknown agent: {agent}")

    config_path = _profile_dir(agent) / "config.yaml"
    if not config_path.exists():
        raise HTTPException(404, f"Config not found for agent '{agent}'")

    # Read current config
    raw = config_path.read_text(encoding="utf-8")
    config = yaml.safe_load(raw) or {}
    if "model" not in config:
        config["model"] = {}

    # Apply updates
    if update.model is not None:
        config["model"]["default"] = update.model
    if update.provider is not None:
        config["model"]["provider"] = update.provider

    # Write back
    config_path.write_text(yaml.dump(config, default_flow_style=False, allow_unicode=True), encoding="utf-8")

    logger.info("Config updated for %s: model=%s provider=%s", agent, update.model, update.provider)
    return {
        "agent": agent,
        "model": config["model"].get("default", ""),
        "provider": config["model"].get("provider", ""),
        "message": "Config saved. Restart agent dashboard to apply.",
    }


@router.get("/config/{agent}/models")
async def config_models(agent: str):
    """Return list of known model identifiers."""
    if agent not in AGENTS:
        raise HTTPException(400, f"Unknown agent: {agent}")
    return {"agent": agent, "models": KNOWN_MODELS}


# ---------------------------------------------------------------------------
# Skills
# ---------------------------------------------------------------------------

@router.get("/skills/{agent}")
async def skills_list(agent: str):
    """List installed skills (global — shared across profiles)."""
    if agent not in AGENTS:
        raise HTTPException(400, f"Unknown agent: {agent}")
    if not _has_hermes():
        raise HTTPException(503, "Hermes CLI not found on this system")

    proc = await asyncio.create_subprocess_exec(
        "hermes", "skills", "list",
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=15)
    output = stdout.decode(errors="replace")
    if proc.returncode != 0:
        raise HTTPException(500, detail=stderr.decode(errors="replace")[:500])

    # Parse table output — skip header lines, extract skill names
    skills = []
    for line in output.strip().split("\n"):
        line = line.strip()
        if not line or line.startswith("┌") or line.startswith("│ Name") or line.startswith("├") or line.startswith("└"):
            continue
        parts = line.split("│")
        if len(parts) >= 2:
            name = parts[1].strip()
            if name:
                skills.append(name)

    return {"agent": agent, "skills": skills}


@router.post("/skills/{agent}/install")
async def skills_install(agent: str, request: SkillInstallRequest):
    """Install a skill from the Hermes skill hub."""
    if agent not in AGENTS:
        raise HTTPException(400, f"Unknown agent: {agent}")
    if not _has_hermes():
        raise HTTPException(503, "Hermes CLI not found on this system")

    proc = await asyncio.create_subprocess_exec(
        "hermes", "skills", "install", request.skill_id,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=30)
    if proc.returncode != 0:
        raise HTTPException(500, detail=stderr.decode(errors="replace")[:500])

    return {"agent": agent, "message": stdout.decode(errors="replace").strip()}


# ---------------------------------------------------------------------------
# Chat
# ---------------------------------------------------------------------------

@router.post("/chat/{agent}")
async def hermes_chat(agent: str, request: ChatRequest):
    """Chat directly with a Hermes Agent profile via CLI."""
    if agent not in AGENTS:
        raise HTTPException(400, f"Unknown agent: {agent}")
    if not _has_hermes():
        raise HTTPException(503, "Hermes CLI not found on this system")

    profile = AGENTS[agent]["profile"]
    skill = AGENTS[agent]["skill"]

    proc = await asyncio.create_subprocess_exec(
        "hermes", "-p", profile,
        "chat", "-q", request.text,
        "-s", skill,
        "--quiet",
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )

    try:
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=60)
    except asyncio.TimeoutError:
        proc.kill()
        await proc.wait()
        raise HTTPException(504, f"Chat with '{agent}' timed out after 60s")

    if proc.returncode != 0:
        err = stderr.decode(errors="replace").strip()
        raise HTTPException(500, detail=f"Hermes agent '{agent}' failed (exit {proc.returncode}): {err}")

    output = stdout.decode(errors="replace").strip()

    # Strip session_id prefix line
    output = re.sub(r"^session_id:\s*\S+\s*\n?", "", output).strip()
    # Strip code fences
    output = re.sub(r"^```\w*\n?", "", output)
    output = re.sub(r"\n?```$", "", output)

    return {"agent": agent, "profile": profile, "response": output.strip()}
