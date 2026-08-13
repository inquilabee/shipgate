"""Tests for project root cache discovery."""

from pathlib import Path

import pytest

from shipgate.paths import (
    PROJECT_CACHE_ENV,
    SHIPGATE_DIR,
    contained_child,
    find_cached_project_root,
    find_project_root,
    normalize_finding_path,
    parse_env_file,
    read_cached_project_root,
)
from shipgate.project.init import init_project


def test_init_writes_project_root_cache(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.delenv("VIRTUAL_ENV", raising=False)
    init_project(tmp_path)
    env_path = tmp_path / PROJECT_CACHE_ENV
    assert env_path.is_file()
    assert parse_env_file(env_path) == {
        "SHIPGATE_POLICY": "yaml",
        "SHIPGATE_ROOT": str(tmp_path.resolve()),
    }


def test_init_gitignore_ignores_cache(tmp_path: Path) -> None:
    init_project(tmp_path)
    gitignore = (tmp_path / SHIPGATE_DIR / ".gitignore").read_text(encoding="utf-8")
    assert "cache/" in gitignore


def test_find_project_root_uses_cache_without_yaml(tmp_path: Path) -> None:
    nested = tmp_path / "nested" / "deep"
    nested.mkdir(parents=True)
    env_path = tmp_path / PROJECT_CACHE_ENV
    env_path.parent.mkdir(parents=True)
    env_path.write_text(f"SHIPGATE_ROOT={tmp_path.resolve()}\n", encoding="utf-8")
    assert find_project_root(nested) == tmp_path.resolve()


def test_find_cached_project_root_skips_missing_path(tmp_path: Path) -> None:
    env_path = tmp_path / PROJECT_CACHE_ENV
    env_path.parent.mkdir(parents=True)
    env_path.write_text("SHIPGATE_ROOT=/does/not/exist\n", encoding="utf-8")
    assert read_cached_project_root(env_path) is None
    assert find_cached_project_root(tmp_path) is None


def test_find_project_root_cache_beats_nested_git(tmp_path: Path) -> None:
    child = tmp_path / "child"
    nested = child / "nested"
    nested.mkdir(parents=True)
    (child / ".git").mkdir()
    env_path = tmp_path / PROJECT_CACHE_ENV
    env_path.parent.mkdir(parents=True)
    env_path.write_text(f"SHIPGATE_ROOT={tmp_path.resolve()}\n", encoding="utf-8")
    assert find_project_root(nested) == tmp_path.resolve()


def test_reset_radon_cache_env_drops_radon_keys_only(tmp_path: Path) -> None:
    from shipgate.paths import (
        POLICY_CACHE_KEY,
        PROJECT_ROOT_CACHE_KEY,
        RADON_CC_P95_CACHE_ENV,
        RADON_MI_MEDIAN_CACHE_ENV,
        reset_radon_cache_env,
        update_project_cache_env,
    )

    update_project_cache_env(
        tmp_path,
        {
            PROJECT_ROOT_CACHE_KEY: str(tmp_path.resolve()),
            POLICY_CACHE_KEY: "yaml",
            RADON_MI_MEDIAN_CACHE_ENV: "55.0",
            RADON_CC_P95_CACHE_ENV: "7",
        },
    )
    reset_radon_cache_env(tmp_path)
    values = parse_env_file(tmp_path / PROJECT_CACHE_ENV)
    assert values[PROJECT_ROOT_CACHE_KEY] == str(tmp_path.resolve())
    assert values[POLICY_CACHE_KEY] == "yaml"
    assert RADON_MI_MEDIAN_CACHE_ENV not in values
    assert RADON_CC_P95_CACHE_ENV not in values
    assert not any(key.startswith("SHIPGATE_RADON_") for key in values)


def test_contained_child_rejects_escape(tmp_path: Path) -> None:
    nested = contained_child(tmp_path, "configs/ruff.toml")
    assert nested.is_relative_to(tmp_path.resolve())
    with pytest.raises(ValueError, match="escapes"):
        contained_child(tmp_path, "../x")
    with pytest.raises(ValueError, match="escapes"):
        contained_child(tmp_path, "/etc/passwd")
    with pytest.raises(ValueError, match="escapes"):
        contained_child(tmp_path, "")


def test_contained_child_does_not_follow_leaf_symlink(tmp_path: Path) -> None:
    outside = tmp_path / "outside"
    outside.write_text("x", encoding="utf-8")
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    (bin_dir / "gitleaks").symlink_to(outside)
    result = contained_child(bin_dir, "gitleaks")
    assert result == bin_dir.resolve() / "gitleaks"
    assert result.is_relative_to(bin_dir.resolve())


def test_normalize_finding_path_joins_project_root(tmp_path: Path, monkeypatch) -> None:
    other = tmp_path / "cwd"
    other.mkdir()
    project = tmp_path / "proj"
    project.mkdir()
    (project / "foo.py").write_text("x = 1\n", encoding="utf-8")
    monkeypatch.chdir(other)
    assert normalize_finding_path("foo.py", project_root=project) == "foo.py"
    assert normalize_finding_path("../secret.py", project_root=project) is None


def test_reset_radon_cache_env_missing_file_is_noop(tmp_path: Path) -> None:
    from shipgate.paths import reset_radon_cache_env

    path = reset_radon_cache_env(tmp_path)
    assert not path.is_file()
