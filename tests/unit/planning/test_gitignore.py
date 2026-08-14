from pathlib import Path

from shipgate.domain.modes import RunMode
from shipgate.domain.project import Scope
from shipgate.planning.core.scope_resolver import DEFAULT_EXCLUDES
from shipgate.planning.core.scopes import scope_paths
from shipgate.planning.utils.gitignore import (
    default_ignores,
    expand_scope,
    include_allowed,
    matches_tool_criteria,
    should_ignore,
)


def test_should_ignore_shipgate_dir(tmp_path: Path):
    ignored = tmp_path / ".shipgate" / "cache"
    ignored.mkdir(parents=True)
    assert should_ignore(tmp_path, ignored)


def test_should_ignore_venv_dirs(tmp_path: Path):
    dot_venv = tmp_path / ".venv" / "lib"
    dot_venv.mkdir(parents=True)
    plain_venv = tmp_path / "venv" / "lib"
    plain_venv.mkdir(parents=True)
    review_venv = tmp_path / ".review-venv" / "lib" / "python3.13" / "site-packages" / "rich"
    review_venv.mkdir(parents=True)
    assert should_ignore(tmp_path, dot_venv)
    assert should_ignore(tmp_path, plain_venv)
    assert should_ignore(tmp_path, review_venv)


def test_should_ignore_root_reports_not_nested_package(tmp_path: Path):
    root_report = tmp_path / "reports" / "out.txt"
    root_report.parent.mkdir()
    root_report.write_text("x\n", encoding="utf-8")
    nested = tmp_path / "src" / "pkg" / "reports" / "mod.py"
    nested.parent.mkdir(parents=True)
    nested.write_text("x = 1\n", encoding="utf-8")
    assert should_ignore(tmp_path, root_report)
    assert not should_ignore(tmp_path, nested)


def test_should_not_ignore_prevenv_package_dir(tmp_path: Path):
    path = tmp_path / "src" / "prevenv" / "mod.py"
    path.parent.mkdir(parents=True)
    path.write_text("x = 1\n", encoding="utf-8")
    assert not should_ignore(tmp_path, path)


def test_should_ignore_git_info_exclude(tmp_path: Path):
    git_dir = tmp_path / ".git" / "info"
    git_dir.mkdir(parents=True)
    (git_dir / "exclude").write_text("scratch/\n", encoding="utf-8")
    leaked = tmp_path / "scratch" / "notes.py"
    leaked.parent.mkdir()
    leaked.write_text("y = 1\n", encoding="utf-8")
    assert should_ignore(tmp_path, leaked)


def test_expand_scope_respects_gitignore(tmp_path: Path):
    (tmp_path / ".gitignore").write_text("ignored/\n", encoding="utf-8")
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "ok.py").write_text("x = 1\n", encoding="utf-8")
    ignored = tmp_path / "ignored"
    ignored.mkdir()
    (ignored / "bad.py").write_text("y = 2\n", encoding="utf-8")
    paths = expand_scope(tmp_path, tmp_path)
    names = {p.name for p in paths}
    assert "ok.py" in names
    assert "bad.py" not in names


def test_expand_scope_skips_node_modules_without_gitignore(tmp_path: Path):
    nested = tmp_path / "node_modules" / "pkg"
    nested.mkdir(parents=True)
    (nested / "x.py").write_text("x = 1\n", encoding="utf-8")
    (tmp_path / "ok.py").write_text("y = 1\n", encoding="utf-8")
    paths = expand_scope(tmp_path, tmp_path, respect_gitignore=False)
    names = {p.name for p in paths}
    assert "ok.py" in names
    assert "x.py" not in names


def test_expand_scope_exclude_applies_without_gitignore(tmp_path: Path):
    scratch = tmp_path / "scratch"
    scratch.mkdir()
    (scratch / "site.py").write_text("x = 1\n", encoding="utf-8")
    (tmp_path / "ok.py").write_text("y = 1\n", encoding="utf-8")
    paths = expand_scope(tmp_path, tmp_path, exclude=("scratch/",), respect_gitignore=False)
    names = {p.name for p in paths}
    assert "ok.py" in names
    assert "site.py" not in names


def test_scope_paths_for_tool_respect_gitignore_false_keeps_gitignored(
    tmp_path: Path,
):
    from shipgate.domain.catalog import ScopeCriteria, ToolDefinition
    from shipgate.planning.core.scopes import scope_paths_for_tool

    (tmp_path / ".gitignore").write_text("scratch/\n", encoding="utf-8")
    scratch = tmp_path / "scratch"
    scratch.mkdir()
    (scratch / "a.md").write_text("x\n", encoding="utf-8")
    venv = tmp_path / ".venv"
    venv.mkdir()
    (venv / "x.md").write_text("y\n", encoding="utf-8")
    (tmp_path / "kept.md").write_text("z\n", encoding="utf-8")
    tool = ToolDefinition(
        id="md.format",
        executable="mdformat",
        scope=ScopeCriteria(extensions=(".md",), delivery="files"),
    )
    scope = Scope(
        target=tmp_path,
        exclude=(".venv/",),
        respect_gitignore=False,
    )
    paths = scope_paths_for_tool(scope, tool, tmp_path, mode=RunMode.CHECK)
    names = {Path(p).name for p in paths}
    assert "a.md" in names
    assert "kept.md" in names
    assert "x.md" not in names


def test_scope_paths_check_outside_root_is_empty(tmp_path: Path):
    outside = tmp_path.parent / f"outside-check-{tmp_path.name}"
    outside.mkdir()
    scope = Scope(target=outside, respect_gitignore=False, exclude=(), include=())
    assert scope_paths(scope, tmp_path, mode=RunMode.CHECK) == ()


def test_include_allowed_uses_path_prefix():
    assert include_allowed("src/a.py", ("src",))
    assert include_allowed("src", ("src",))
    assert not include_allowed("src_backup/a.py", ("src",))
    assert not include_allowed("src_backup/a.py", ("src/",))


def test_default_excludes_reuse_default_ignores_plus_build():
    assert (*default_ignores(), "build/") == DEFAULT_EXCLUDES
    assert ".review-venv/" in DEFAULT_EXCLUDES
    assert "site-packages/" in DEFAULT_EXCLUDES


def test_expand_scope_include_does_not_match_prefix_sibling(tmp_path: Path):
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "ok.py").write_text("x = 1\n", encoding="utf-8")
    backup = tmp_path / "src_backup"
    backup.mkdir()
    (backup / "no.py").write_text("y = 2\n", encoding="utf-8")
    paths = expand_scope(tmp_path, tmp_path, include=("src",))
    names = {p.name for p in paths}
    assert "ok.py" in names
    assert "no.py" not in names


def test_scope_paths_include_does_not_match_prefix_sibling(tmp_path: Path):
    (tmp_path / "src").mkdir()
    (tmp_path / "src_backup").mkdir()
    scope = Scope(target=tmp_path, include=("src",), respect_gitignore=True)
    paths = scope_paths(scope, tmp_path, mode=RunMode.CHECK)
    assert paths == (tmp_path / "src",)


def test_scope_paths_nested_target_rejects_include_prefix_sibling(tmp_path: Path):
    (tmp_path / "src").mkdir()
    backup = tmp_path / "src_backup"
    backup.mkdir()
    scope = Scope(target=backup, include=("src",), respect_gitignore=True)
    paths = scope_paths(scope, tmp_path, mode=RunMode.CHECK)
    assert backup not in paths


def test_scope_paths_apply_outside_root_is_empty(tmp_path: Path):
    outside = tmp_path.parent / f"outside-apply-{tmp_path.name}"
    outside.mkdir()
    scope = Scope(target=outside, respect_gitignore=True)
    assert scope_paths(scope, tmp_path, mode=RunMode.APPLY) == ()


def test_matches_tool_criteria_glob():
    rel = ".cursor/rules/foo.mdc"
    assert matches_tool_criteria(rel, globs=("**/*.mdc",))
    assert not matches_tool_criteria("docs/readme.md", globs=("**/*.mdc",))
