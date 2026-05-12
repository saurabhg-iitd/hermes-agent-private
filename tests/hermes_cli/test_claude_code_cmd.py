"""Tests for ``hermes_cli.claude_code_cmd``."""

import sys
from unittest.mock import patch

import pytest


def test_resolve_claude_code_executable_prefers_hermes_env(tmp_path, monkeypatch):
    from hermes_cli import claude_code_cmd as m

    fake = tmp_path / "claude-test"
    fake.write_text("#!/bin/sh\necho ok\n")
    fake.chmod(0o755)
    monkeypatch.delenv("CLAUDE_CODE_BIN", raising=False)
    monkeypatch.setenv("HERMES_CLAUDE_CODE_BIN", str(fake))
    assert m.resolve_claude_code_executable() == str(fake)


def test_resolve_claude_code_executable_which_name(monkeypatch):
    from hermes_cli import claude_code_cmd as m

    monkeypatch.delenv("HERMES_CLAUDE_CODE_BIN", raising=False)
    monkeypatch.delenv("CLAUDE_CODE_BIN", raising=False)
    with patch.object(m.shutil, "which", return_value="/usr/bin/claude") as wh:
        assert m.resolve_claude_code_executable() == "/usr/bin/claude"
    wh.assert_called_once_with("claude")


def test_resolve_falls_back_to_dot_local_bin(tmp_path, monkeypatch):
    from hermes_cli import claude_code_cmd as m

    monkeypatch.delenv("HERMES_CLAUDE_CODE_BIN", raising=False)
    monkeypatch.delenv("CLAUDE_CODE_BIN", raising=False)
    monkeypatch.setattr(m.shutil, "which", lambda *_a, **_k: None)

    home = tmp_path / "h"
    bin_dir = home / ".local" / "bin"
    bin_dir.mkdir(parents=True)
    exe = bin_dir / "claude"
    exe.write_text("#!/bin/sh\necho\n")
    exe.chmod(0o755)
    monkeypatch.setenv("HOME", str(home))

    assert m.resolve_claude_code_executable() == str(exe.resolve())


def test_cmd_claude_code_exec_invokes_claude_argv(monkeypatch):
    from hermes_cli.claude_code_cmd import cmd_claude_code

    ns = type("Args", (), {"claude_argv": ["-p", "hi"]})()

    def fake_execvp(path, argv):
        assert path == "/x/claude"
        assert argv == ["/x/claude", "-p", "hi"]
        sys.exit(99)

    monkeypatch.setattr("hermes_cli.claude_code_cmd.resolve_claude_code_executable", lambda: "/x/claude")
    monkeypatch.setattr("hermes_cli.claude_code_cmd.os.execvp", fake_execvp)
    with pytest.raises(SystemExit) as ei:
        cmd_claude_code(ns)
    assert ei.value.code == 99


def test_cmd_claude_code_strips_leading_double_dash(monkeypatch):
    from hermes_cli.claude_code_cmd import cmd_claude_code

    ns = type("Args", (), {"claude_argv": ["--", "-p", "x"]})()

    def fake_execvp(path, argv):
        assert argv == ["/c", "-p", "x"]
        sys.exit(7)

    monkeypatch.setattr("hermes_cli.claude_code_cmd.resolve_claude_code_executable", lambda: "/c")
    monkeypatch.setattr("hermes_cli.claude_code_cmd.os.execvp", fake_execvp)
    with pytest.raises(SystemExit) as ei:
        cmd_claude_code(ns)
    assert ei.value.code == 7


def test_cmd_claude_code_subprocess_fallback(monkeypatch):
    from hermes_cli.claude_code_cmd import cmd_claude_code

    ns = type("Args", (), {"claude_argv": []})()
    monkeypatch.setattr("hermes_cli.claude_code_cmd.resolve_claude_code_executable", lambda: "/c")

    def boom_execvp(path, argv):
        raise OSError("exec not supported")

    class Proc:
        returncode = 42

    monkeypatch.setattr("hermes_cli.claude_code_cmd.os.execvp", boom_execvp)
    monkeypatch.setattr(
        "hermes_cli.claude_code_cmd.subprocess.run", lambda argv: Proc()
    )
    with pytest.raises(SystemExit) as ei:
        cmd_claude_code(ns)
    assert ei.value.code == 42


def test_cmd_claude_code_missing_binary(monkeypatch, capsys):
    from hermes_cli.claude_code_cmd import cmd_claude_code

    ns = type("Args", (), {"claude_argv": []})()
    monkeypatch.setattr("hermes_cli.claude_code_cmd.resolve_claude_code_executable", lambda: None)
    with pytest.raises(SystemExit) as ei:
        cmd_claude_code(ns)
    assert ei.value.code == 127
    err = capsys.readouterr().err
    assert "Claude Code CLI" in err
