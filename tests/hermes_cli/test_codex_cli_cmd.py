"""Tests for ``hermes_cli.codex_cli_cmd``."""

from unittest.mock import patch


def test_resolve_codex_prefers_env(tmp_path, monkeypatch):
    from hermes_cli import codex_cli_cmd as m

    fake = tmp_path / "codex-test"
    fake.write_text("#!/bin/sh\necho\n")
    fake.chmod(0o755)
    monkeypatch.delenv("CODEX_BIN", raising=False)
    monkeypatch.setenv("HERMES_CODEX_BIN", str(fake))
    assert m.resolve_codex_cli_executable() == str(fake)


def test_resolve_codex_which(monkeypatch):
    from hermes_cli import codex_cli_cmd as m

    monkeypatch.delenv("HERMES_CODEX_BIN", raising=False)
    monkeypatch.delenv("CODEX_BIN", raising=False)
    with patch.object(m.shutil, "which", return_value="/usr/bin/codex") as wh:
        assert m.resolve_codex_cli_executable() == "/usr/bin/codex"
    wh.assert_called_once_with("codex")


def test_resolve_codex_dot_local_bin(tmp_path, monkeypatch):
    from hermes_cli import codex_cli_cmd as m

    monkeypatch.delenv("HERMES_CODEX_BIN", raising=False)
    monkeypatch.delenv("CODEX_BIN", raising=False)
    monkeypatch.setattr(m.shutil, "which", lambda *_a, **_k: None)

    home = tmp_path / "h"
    bin_dir = home / ".local" / "bin"
    bin_dir.mkdir(parents=True)
    exe = bin_dir / "codex"
    exe.write_text("#!/bin/sh\necho\n")
    exe.chmod(0o755)
    monkeypatch.setenv("HOME", str(home))

    assert m.resolve_codex_cli_executable() == str(exe.resolve())
