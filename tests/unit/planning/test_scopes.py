from pathlib import Path

from shipgate.domain.modes import RunMode
from shipgate.domain.project import Scope
from shipgate.planning.scopes import scope_paths


def test_scope_paths_prunes_ignored_roots(tmp_path: Path):
    (tmp_path / ".gitignore").write_text(".venv/\n", encoding="utf-8")
    (tmp_path / "src").mkdir()
    (tmp_path / "docs").mkdir()
    venv = tmp_path / ".venv"
    venv.mkdir()

    scope = Scope(target=tmp_path, respect_gitignore=True)
    paths = scope_paths(scope, tmp_path, mode=RunMode.CHECK)

    names = {p.name for p in paths}
    assert "src" in names
    assert "docs" in names
    assert ".venv" not in names


def test_scope_paths_apply_mode_uses_target(tmp_path: Path):
    (tmp_path / "src").mkdir()
    scope = Scope(target=tmp_path, respect_gitignore=True)
    assert scope_paths(scope, tmp_path, mode=RunMode.APPLY) == (tmp_path,)


def test_scope_paths_keeps_nested_target(tmp_path: Path):
    src = tmp_path / "src"
    src.mkdir()

    scope = Scope(target=src, respect_gitignore=True)
    assert scope_paths(scope, tmp_path, mode=RunMode.CHECK) == (src,)


def test_scope_paths_honors_include(tmp_path: Path):
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "ok.py").write_text("x = 1\n", encoding="utf-8")
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "readme.md").write_text("# hi\n", encoding="utf-8")

    scope = Scope(target=tmp_path, include=("src/",), respect_gitignore=True)
    paths = scope_paths(scope, tmp_path, mode=RunMode.CHECK)

    assert paths == (tmp_path / "src",)


def test_scope_paths_honors_nested_include(tmp_path: Path):
    package = tmp_path / "src" / "reslab"
    package.mkdir(parents=True)
    tests = tmp_path / "src" / "tests"
    tests.mkdir(parents=True)

    scope = Scope(target=tmp_path, include=("src/reslab",), respect_gitignore=True)
    paths = scope_paths(scope, tmp_path, mode=RunMode.CHECK)

    assert paths == (package,)
    assert tests not in paths


def test_scope_paths_returns_target_when_disabled(tmp_path: Path):
    target = tmp_path / "src"
    target.mkdir()
    scope = Scope(target=target, respect_gitignore=False)
    assert scope_paths(scope, tmp_path, mode=RunMode.CHECK) == (target,)
