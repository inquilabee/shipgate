from pathlib import Path

from shipgate.adapter.argv import build_argv
from shipgate.catalog.loader import load_catalog
from shipgate.domain.execution import ExecutionEnvironment
from shipgate.domain.modes import RunMode
from shipgate.domain.options import NormalizedOptions
from shipgate.planning.requests import build_execution_request, resolve_request


def test_ruff_lint_argv(tmp_path):
    catalog = load_catalog()
    tool = catalog.get_tool("ruff.lint")
    request = build_execution_request(
        runnable="ruff.lint",
        mode=RunMode.CHECK,
        project_root=tmp_path,
        options=NormalizedOptions(
            paths=(tmp_path / "src",),
            format="json",
            output=tmp_path / "out.json",
        ),
    )
    env = ExecutionEnvironment(kind="system", root=None, env={})
    resolved = resolve_request(request, tool, env, target=tmp_path)
    argv = build_argv(resolved)
    assert argv[0] == "ruff"
    assert "check" in argv
    assert "--output-format" in argv
    assert str(tmp_path / "src") in argv


def test_ruff_format_check_mode(tmp_path):
    catalog = load_catalog()
    tool = catalog.get_tool("ruff.format")
    request = build_execution_request(
        runnable="ruff.format",
        mode=RunMode.CHECK,
        project_root=tmp_path,
        options=NormalizedOptions(paths=(tmp_path,), check=True),
    )
    env = ExecutionEnvironment(kind="system", root=None, env={})
    resolved = resolve_request(request, tool, env, target=tmp_path)
    argv = build_argv(resolved)
    assert "--check" in argv


def test_mdformat_apply_enables_frontmatter_by_default(tmp_path):
    catalog = load_catalog()
    tool = catalog.get_tool("mdformat.apply")
    request = build_execution_request(
        runnable="mdformat.apply",
        mode=RunMode.CHECK,
        project_root=tmp_path,
        options=NormalizedOptions(paths=(tmp_path / "README.md",), check=True),
    )
    env = ExecutionEnvironment(kind="system", root=None, env={})
    resolved = resolve_request(request, tool, env, target=tmp_path)
    argv = build_argv(resolved)
    extensions_index = argv.index("--extensions")
    assert argv[extensions_index + 1] == "frontmatter"


def test_gitleaks_scan_uses_project_root_for_multiple_scope_paths(tmp_path):
    catalog = load_catalog()
    tool = catalog.get_tool("gitleaks.scan")
    docs = tmp_path / "docs"
    src = tmp_path / "src"
    docs.mkdir()
    src.mkdir()
    request = build_execution_request(
        runnable="gitleaks.scan",
        mode=RunMode.CHECK,
        project_root=tmp_path,
        options=NormalizedOptions(paths=(docs, src)),
    )
    env = ExecutionEnvironment(kind="system", root=None, env={})
    resolved = resolve_request(request, tool, env, target=tmp_path)
    argv = build_argv(resolved)
    assert "--source" in argv
    source_index = argv.index("--source")
    assert argv[source_index + 1] == str(tmp_path)


def test_deadcode_check_passes_exclude_and_scoped_dirs(tmp_path):
    catalog = load_catalog()
    tool = catalog.get_tool("deadcode.check")
    src = tmp_path / "src" / "pkg"
    src.mkdir(parents=True)
    request = build_execution_request(
        runnable="deadcode.check",
        mode=RunMode.CHECK,
        project_root=tmp_path,
        options=NormalizedOptions(
            paths=(Path("src/pkg"),),
            exclude=(".venv/", ".trunk/"),
        ),
    )
    env = ExecutionEnvironment(kind="system", root=None, env={})
    resolved = resolve_request(request, tool, env, target=tmp_path)
    argv = build_argv(resolved)
    assert argv[0] == "deadcode"
    assert "src/pkg" in argv
    exclude_index = argv.index("--exclude")
    assert argv[exclude_index + 1] == ".venv/"
    assert argv[exclude_index + 3] == ".trunk/"
    assert exclude_index > argv.index("src/pkg")
