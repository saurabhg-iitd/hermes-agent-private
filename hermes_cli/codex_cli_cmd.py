"""Resolve the OpenAI Codex CLI (``codex``) binary for Hermes integrations.

Used by ``/agent-configure`` to launch the standalone Codex CLI. Install:
``npm install -g @openai/codex``. See ``skills/autonomous-ai-agents/codex/``.
"""

from __future__ import annotations

import os
import shutil
from pathlib import Path
from typing import Iterable, Optional


def _executable_if_present(path: Path) -> Optional[str]:
    try:
        p = path.expanduser()
    except Exception:
        p = path
    try:
        if p.is_file() and os.access(p, os.X_OK):
            return str(p.resolve())
    except OSError:
        return None
    return None


def _well_known_codex_paths() -> Iterable[Path]:
    home = Path.home()
    yield home / ".local" / "bin" / "codex"
    yield home / ".npm-global" / "bin" / "codex"
    yield home / ".volta" / "bin" / "codex"


def resolve_codex_cli_executable() -> Optional[str]:
    """Return a path to the Codex ``codex`` binary, or ``None`` if absent."""
    for key in ("HERMES_CODEX_BIN", "CODEX_BIN"):
        override = (os.environ.get(key) or "").strip()
        if not override:
            continue
        expanded = os.path.expanduser(override)
        if os.path.isabs(expanded) or os.sep in expanded or (os.altsep and os.altsep in expanded):
            if os.path.isfile(expanded) and os.access(expanded, os.X_OK):
                return expanded
        found = shutil.which(override) or shutil.which(expanded)
        if found:
            return found
        return None
    found = shutil.which("codex")
    if found:
        return found
    for candidate in _well_known_codex_paths():
        resolved = _executable_if_present(candidate)
        if resolved:
            return resolved
    return None
