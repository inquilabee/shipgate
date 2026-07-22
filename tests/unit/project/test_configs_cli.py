"""Tests for configs CLI commands."""

from pathlib import Path

from shipgate.cli import main


def test_configs_sync_creates_missing(tmp_path: Path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    code = main(["configs", "sync"])
    assert code == 0
    assert (tmp_path / ".shipgate/configs/ruff.toml").is_file()


def test_configs_list_shows_resolved_paths(tmp_path: Path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "shipgate.yaml").write_text("suite: python-quality\n", encoding="utf-8")
    main(["configs", "sync"])
    code = main(["configs", "list"])
    assert code == 0


def test_configs_diff_reports_no_differences_after_sync(tmp_path: Path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    main(["configs", "sync"])
    code = main(["configs", "diff"])
    assert code == 0
