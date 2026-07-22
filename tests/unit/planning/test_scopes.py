import json
from pathlib import Path

from shipgate.adapter.config_resolve import bundled_configs_root
from shipgate.catalog.loader import load_catalog
from shipgate.domain.modes import RunMode
from shipgate.domain.project import ProjectConfig, Scope
from shipgate.planning.gitignore import (
    expand_scope,
    matches_tool_criteria,
    minimize_covering_dirs,
)
from shipgate.planning.scope_resolver import ScopeResolver
from shipgate.planning.scopes import scope_paths, scope_paths_for_tool


def test_scope_resolver_default_excludes(tmp_path: Path):
    scope = ScopeResolver(tmp_path).resolve(ProjectConfig())
    assert ".shipgate/" in scope.exclude
    assert ".venv/" in scope.exclude
    assert "venv/" in scope.exclude


def test_jscpd_bundled_config_writes_under_shipgate_reports():
    catalog = load_catalog()
    tool = catalog.get_tool("jscpd.check")
    bundled = tool.configuration.bundled
    assert bundled is not None
    jscpd_config = json.loads((bundled_configs_root() / bundled).read_text(encoding="utf-8"))
    assert jscpd_config["output"] == ".shipgate/reports/jscpd"
    assert ".shipgate/**" in jscpd_config["ignore"]


def test_scope_resolver_resolve_target(tmp_path: Path):
    (tmp_path / "src").mkdir()
    scope = ScopeResolver(tmp_path).resolve(
        ProjectConfig(),
        target_override=tmp_path,
    )
    assert scope.target == tmp_path.resolve()


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
    assert scope_paths(scope, tmp_path, mode=RunMode.APPLY) == (Path(),)


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


def test_scope_paths_for_tool_delivery_root(tmp_path: Path):
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "ok.py").write_text("x = 1\n", encoding="utf-8")
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "readme.md").write_text("# hi\n", encoding="utf-8")
    catalog = load_catalog()
    tool = catalog.get_tool("ruff.lint")
    scope = Scope(target=tmp_path, respect_gitignore=True)
    paths = scope_paths_for_tool(scope, tool, tmp_path, mode=RunMode.CHECK)
    assert paths == (Path(),)


def test_scope_paths_for_tool_delivery_files(tmp_path: Path):
    (tmp_path / "README.md").write_text("# hi\n", encoding="utf-8")
    (tmp_path / "notes.txt").write_text("plain\n", encoding="utf-8")
    catalog = load_catalog()
    tool = catalog.get_tool("markdownlint.check")
    scope = Scope(target=tmp_path, respect_gitignore=True)
    paths = scope_paths_for_tool(scope, tool, tmp_path, mode=RunMode.CHECK)
    assert paths == (Path("README.md"),)


def test_scope_paths_for_tool_empty_scope_short_circuit(tmp_path: Path):
    (tmp_path / "notes.txt").write_text("plain\n", encoding="utf-8")
    catalog = load_catalog()
    tool = catalog.get_tool("markdownlint.check")
    scope = Scope(target=tmp_path, respect_gitignore=True)
    paths = scope_paths_for_tool(scope, tool, tmp_path, mode=RunMode.CHECK)
    assert paths == ()


def test_scope_paths_for_tool_delivery_dirs(tmp_path: Path):
    package = tmp_path / "src" / "pkg"
    package.mkdir(parents=True)
    (package / "a.py").write_text("x = 1\n", encoding="utf-8")
    (package / "b.py").write_text("y = 2\n", encoding="utf-8")
    catalog = load_catalog()
    tool = catalog.get_tool("gate.folder-breadth")
    scope = Scope(target=tmp_path, respect_gitignore=True)
    paths = scope_paths_for_tool(scope, tool, tmp_path, mode=RunMode.CHECK)
    assert paths == (Path("src/pkg"),)


def test_deadcode_dirs_respects_include(tmp_path: Path):
    included = tmp_path / "src" / "reslab"
    included.mkdir(parents=True)
    (included / "ok.py").write_text("x = 1\n", encoding="utf-8")
    (tmp_path / "src" / "tests").mkdir(parents=True)
    (tmp_path / "src" / "tests" / "bad.py").write_text("y = 2\n", encoding="utf-8")
    tool = load_catalog().get_tool("deadcode.check")
    scope = Scope(target=tmp_path, include=("src/reslab",), respect_gitignore=True)
    assert scope_paths_for_tool(scope, tool, tmp_path, mode=RunMode.CHECK) == (Path("src/reslab"),)


def test_minimize_covering_dirs_prunes_nested(tmp_path: Path):
    files = (
        tmp_path / "src" / "pkg" / "a.py",
        tmp_path / "src" / "pkg" / "b.py",
        tmp_path / "docs" / "readme.md",
    )
    for file_path in files:
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text("x\n", encoding="utf-8")
    dirs = minimize_covering_dirs(files, tmp_path)
    assert dirs == (Path("docs"), Path("src/pkg"))


def test_matches_tool_criteria_extensions_and_globs():
    assert matches_tool_criteria("src/a.py", extensions=(".py",))
    assert not matches_tool_criteria("src/a.md", extensions=(".py",))
    assert matches_tool_criteria(".cursor/rules/foo.mdc", globs=("**/*.mdc",))


def test_expand_scope_filters_extensions(tmp_path: Path):
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "ok.py").write_text("x = 1\n", encoding="utf-8")
    (tmp_path / "src" / "readme.md").write_text("# hi\n", encoding="utf-8")
    paths = expand_scope(tmp_path, tmp_path, extensions=(".py",))
    names = {path.name for path in paths}
    assert names == {"ok.py"}


def test_scope_paths_for_tool_excludes_venv_yaml(tmp_path: Path):
    (tmp_path / ".gitignore").write_text(".venv/\n", encoding="utf-8")
    (tmp_path / "config.yaml").write_text("key: value\n", encoding="utf-8")
    venv = tmp_path / ".venv"
    venv.mkdir()
    (venv / "ignored.yaml").write_text("key: ignored\n", encoding="utf-8")
    catalog = load_catalog()
    tool = catalog.get_tool("yamlfmt.apply")
    scope = Scope(target=tmp_path, respect_gitignore=True)
    paths = scope_paths_for_tool(scope, tool, tmp_path, mode=RunMode.CHECK)
    assert paths == (Path("config.yaml"),)


def test_expand_scope_include_prefix(tmp_path: Path):
    included = tmp_path / "src" / "reslab"
    included.mkdir(parents=True)
    (included / "ok.py").write_text("x = 1\n", encoding="utf-8")
    excluded = tmp_path / "src" / "tests"
    excluded.mkdir(parents=True)
    (excluded / "bad.py").write_text("y = 2\n", encoding="utf-8")
    paths = expand_scope(
        tmp_path,
        tmp_path,
        include=("src/reslab",),
        extensions=(".py",),
    )
    assert paths == (included / "ok.py",)
