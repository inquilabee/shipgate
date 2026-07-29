from shipgate.adapter.argv import build_argv
from shipgate.catalog.loader import CatalogLoader
from shipgate.domain.execution import ExecutionEnvironment
from shipgate.domain.modes import RunMode
from shipgate.domain.options import NormalizedOptions
from shipgate.planning.core.requests import build_execution_request, resolve_request


def test_ruff_lint_argv(tmp_path):
    catalog = CatalogLoader.load()
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
    assert "--fix" not in argv
    assert "--output-format" in argv
    assert str(tmp_path / "src") in argv


def test_ruff_lint_apply_argv(tmp_path):
    catalog = CatalogLoader.load()
    tool = catalog.get_tool("ruff.lint")
    request = build_execution_request(
        runnable="ruff.lint",
        mode=RunMode.APPLY,
        project_root=tmp_path,
        options=NormalizedOptions(paths=(tmp_path / "src",)),
    )
    env = ExecutionEnvironment(kind="system", root=None, env={})
    resolved = resolve_request(request, tool, env, target=tmp_path)
    argv = build_argv(resolved)
    assert argv[0] == "ruff"
    assert "check" in argv
    assert "--fix" in argv
    assert str(tmp_path / "src") in argv


def test_ruff_format_check_mode(tmp_path):
    catalog = CatalogLoader.load()
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


def test_shfmt_apply_matches_external_tool_flags(tmp_path):
    catalog = CatalogLoader.load()
    tool = catalog.get_tool("shfmt.apply")
    script = tmp_path / "script.sh"
    script.write_text("#!/bin/bash\necho hi\n", encoding="utf-8")
    request = build_execution_request(
        runnable="shfmt.apply",
        mode=RunMode.APPLY,
        project_root=tmp_path,
        options=NormalizedOptions(paths=(script,)),
    )
    env = ExecutionEnvironment(kind="system", root=None, env={})
    resolved = resolve_request(request, tool, env, target=tmp_path)
    argv = build_argv(resolved)
    assert argv[:4] == ("shfmt", "-w", "-s", str(script))


def test_shfmt_check_uses_diff_without_write(tmp_path):
    catalog = CatalogLoader.load()
    tool = catalog.get_tool("shfmt.apply")
    script = tmp_path / "script.sh"
    script.write_text("#!/bin/bash\necho hi\n", encoding="utf-8")
    request = build_execution_request(
        runnable="shfmt.apply",
        mode=RunMode.CHECK,
        project_root=tmp_path,
        options=NormalizedOptions(paths=(script,), check=True),
    )
    env = ExecutionEnvironment(kind="system", root=None, env={})
    resolved = resolve_request(request, tool, env, target=tmp_path)
    argv = build_argv(resolved)
    assert "-s" in argv
    assert "-d" in argv
    assert "-w" not in argv


def test_mdformat_apply_enables_frontmatter_by_default(tmp_path):
    catalog = CatalogLoader.load()
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


def test_ty_check_passes_config_file(tmp_path):
    catalog = CatalogLoader.load()
    tool = catalog.get_tool("ty.check")
    config_path = tmp_path / ".shipgate" / "configs" / "ty.toml"
    config_path.parent.mkdir(parents=True)
    config_path.write_text('[environment]\npython = ".venv"\n', encoding="utf-8")
    request = build_execution_request(
        runnable="ty.check",
        mode=RunMode.CHECK,
        project_root=tmp_path,
        options=NormalizedOptions(
            paths=(tmp_path,),
            config=(config_path,),
            exclude=("tests",),
        ),
    )
    env = ExecutionEnvironment(kind="system", root=None, env={})
    resolved = resolve_request(request, tool, env, target=tmp_path)
    argv = build_argv(resolved)
    assert "--config-file" in argv
    assert str(config_path.resolve()) in argv


def test_gitleaks_scan_uses_project_root_for_multiple_scope_paths(tmp_path):
    catalog = CatalogLoader.load()
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
