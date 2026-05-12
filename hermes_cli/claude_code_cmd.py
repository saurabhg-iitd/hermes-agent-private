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
from typing import List, Optional


def resolve_claude_code_executable() -> Optional[str]:
    """Return a path to the Claude Code ``claude`` binary, or ``None`` if absent."""
    for key in ("HERMES_CLAUDE_CODE_BIN", "CLAUDE_CODE_BIN"):
        override = (os.environ.get(key) or "").strip()
        if not override:
            continue
        if os.path.isabs(override) or os.sep in override or (os.altsep and os.altsep in override):
            if os.path.isfile(override) and os.access(override, os.X_OK):
                return override
        found = shutil.which(override)
        if found:
            return found
        return None
    return shutil.which("claude")


def cmd_claude_code(args) -> None:
    """Exec ``claude`` with arguments from ``args.claude_argv`` (REMAINDER)."""
    exe = resolve_claude_code_executable()
    if not exe:
        print(
            "hermes claude-code: could not find the Claude Code CLI on PATH.\n"
            "\n"
            "Install: npm install -g @anthropic-ai/claude-code\n"
            "\n"
            "Or set HERMES_CLAUDE_CODE_BIN to the ``claude`` executable path.",
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
