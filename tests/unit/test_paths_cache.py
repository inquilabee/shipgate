"""Tests for project root cache discovery."""

from pathlib import Path

from shipgate.paths import (
    find_cached_project_root,
    find_project_root,
    parse_env_file,
    project_root_cache_env_path,
    read_cached_project_root,
    shipgate_dir,
)
from shipgate.project.init import init_project


def test_init_writes_project_root_cache(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.delenv("VIRTUAL_ENV", raising=False)
    init_project(tmp_path)
    env_path = project_root_cache_env_path(tmp_path)
    assert env_path.is_file()
    assert parse_env_file(env_path) == {
        "SHIPGATE_POLICY": "yaml",
        "SHIPGATE_ROOT": str(tmp_path.resolve()),
    }


def test_init_gitignore_ignores_cache(tmp_path: Path) -> None:
    init_project(tmp_path)
    gitignore = (shipgate_dir(tmp_path) / ".gitignore").read_text(encoding="utf-8")
    assert "cache/" in gitignore


def test_find_project_root_uses_cache_without_yaml(tmp_path: Path) -> None:
    nested = tmp_path / "nested" / "deep"
    nested.mkdir(parents=True)
    env_path = project_root_cache_env_path(tmp_path)
    env_path.parent.mkdir(parents=True)
    env_path.write_text(f"SHIPGATE_ROOT={tmp_path.resolve()}\n", encoding="utf-8")
    assert find_project_root(nested) == tmp_path.resolve()


def test_find_cached_project_root_skips_missing_path(tmp_path: Path) -> None:
    env_path = project_root_cache_env_path(tmp_path)
    env_path.parent.mkdir(parents=True)
    env_path.write_text("SHIPGATE_ROOT=/does/not/exist\n", encoding="utf-8")
    assert read_cached_project_root(env_path) is None
    assert find_cached_project_root(tmp_path) is None


def test_find_project_root_cache_beats_nested_git(tmp_path: Path) -> None:
    child = tmp_path / "child"
    nested = child / "nested"
    nested.mkdir(parents=True)
    (child / ".git").mkdir()
    env_path = project_root_cache_env_path(tmp_path)
    env_path.parent.mkdir(parents=True)
    env_path.write_text(f"SHIPGATE_ROOT={tmp_path.resolve()}\n", encoding="utf-8")
    assert find_project_root(nested) == tmp_path.resolve()
