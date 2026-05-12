"""Passthrough to Anthropic's Claude Code CLI (``claude``).

``hermes claude-code …`` / ``hermes cc …`` replaces the current process with
``claude …`` when possible so interactive TTY behavior matches running Claude
Code directly. See bundled skill ``skills/autonomous-ai-agents/claude-code/``.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Iterable, List, Optional


def _executable_if_present(path: Path) -> Optional[str]:
    """Return ``path`` as a string if it exists and is executable, else ``None``."""
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


def _well_known_claude_paths() -> Iterable[Path]:
    """Locations often missing from a minimal PATH (e.g. ``uv run``, CI, IDEs)."""
    home = Path.home()
    yield home / ".local" / "bin" / "claude"
    yield home / ".npm-global" / "bin" / "claude"
    yield home / ".volta" / "bin" / "claude"
    # Windows native installs sometimes land here
    local = os.environ.get("LOCALAPPDATA", "")
    if local:
        yield Path(local) / "Programs" / "Claude" / "claude.exe"


def resolve_claude_code_executable() -> Optional[str]:
    """Return a path to the Claude Code ``claude`` binary, or ``None`` if absent."""
    for key in ("HERMES_CLAUDE_CODE_BIN", "CLAUDE_CODE_BIN"):
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
    found = shutil.which("claude")
    if found:
        return found
    for candidate in _well_known_claude_paths():
        resolved = _executable_if_present(candidate)
        if resolved:
            return resolved
    return None


def cmd_claude_code(args) -> None:
    """Exec ``claude`` with arguments from ``args.claude_argv`` (REMAINDER)."""
    exe = resolve_claude_code_executable()
    if not exe:
        print(
            "hermes claude-code: could not find the Claude Code CLI.\n"
            "\n"
            "Install: npm install -g @anthropic-ai/claude-code\n"
            "\n"
            "If ``claude`` is already installed (often under ~/.local/bin) but this\n"
            "command still fails, add that directory to PATH or set:\n"
            "  export HERMES_CLAUDE_CODE_BIN=\"$(command -v claude)\"\n",
            file=sys.stderr,
        )
        raise SystemExit(127)

    forward: List[str] = list(getattr(args, "claude_argv", None) or [])
    if forward and forward[0] == "--":
        forward = forward[1:]

    argv = [exe] + forward
    try:
        os.execvp(exe, argv)
    except OSError as exc:
        print(f"hermes claude-code: exec failed ({exe}): {exc}", file=sys.stderr)
        try:
            completed = subprocess.run(argv)
        except OSError as exc2:
            print(f"hermes claude-code: spawn failed: {exc2}", file=sys.stderr)
            raise SystemExit(126) from exc2
        raise SystemExit(completed.returncode) from exc
