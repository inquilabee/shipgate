import pytest

from shipgate.catalog.loader import CatalogLoader
from shipgate.domain.modes import RunMode
from shipgate.domain.project import CheckBinding, ProjectConfig
from shipgate.errors import PlanningError
from shipgate.planning.core.suites import expand_suite
from shipgate.planning.workflow import resolve_runnables, suite_execution_flags


@pytest.fixture
def catalog():
    return CatalogLoader.load()


def test_default_selects_standard(catalog):
    suite_id, selected = resolve_runnables(
        mode=RunMode.CHECK,
        project=ProjectConfig(),
        catalog=catalog,
    )
    assert suite_id == "standard"
    assert [item.tool_id for item in selected] == ["ruff.lint", "ty.check"]


def test_suite_override(catalog):
    _, selected = resolve_runnables(
        mode=RunMode.CHECK,
        project=ProjectConfig(),
        catalog=catalog,
        suite_override="python-quality",
    )
    assert [item.tool_id for item in selected] == ["ruff.lint", "ty.check"]


def test_suite_override_beats_project_suite(catalog):
    project = ProjectConfig(suite="standard")
    suite_id, selected = resolve_runnables(
        mode=RunMode.CHECK,
        project=project,
        catalog=catalog,
        suite_override="python-quality",
    )
    assert suite_id == "python-quality"
    assert [item.tool_id for item in selected] == ["ruff.lint", "ty.check"]


def test_check_override(catalog):
    suite_id, selected = resolve_runnables(
        mode=RunMode.CHECK,
        project=ProjectConfig(),
        catalog=catalog,
        check_override="ruff.lint",
    )
    assert suite_id == "ruff.lint"
    assert [item.tool_id for item in selected] == ["ruff.lint"]


def test_unknown_suite_fails(catalog):
    with pytest.raises(PlanningError):
        resolve_runnables(
            mode=RunMode.CHECK,
            project=ProjectConfig(),
            catalog=catalog,
            suite_override="nope",
        )


def test_nested_suite_expands(catalog):
    tools = expand_suite("standard", catalog)
    assert tools == ["ruff.lint", "ty.check"]


def test_duplicate_leaves_deduped(catalog):
    catalog_data = catalog
    tools = expand_suite("full", catalog_data)
    assert tools.count("ruff.lint") == 1


def test_extended_suite_includes_radon_mi_and_jscpd(catalog):
    tools = expand_suite("extended", catalog)
    assert "radon.cc" in tools
    assert "radon.mi" in tools
    assert "jscpd.check.python" in tools
    assert "jscpd.check.other" in tools


def test_ci_suite_resolves(catalog):
    suite_id, selected = resolve_runnables(
        mode=RunMode.CHECK,
        project=ProjectConfig(),
        catalog=catalog,
        suite_override="ci",
    )
    assert suite_id == "ci"
    assert [item.tool_id for item in selected][:2] == ["ruff.lint", "ty.check"]


def test_format_suite_runs_ruff_lint_before_format(catalog):
    suite_id, selected = resolve_runnables(
        mode=RunMode.APPLY,
        project=ProjectConfig(),
        catalog=catalog,
    )
    assert suite_id == "format"
    assert [item.tool_id for item in selected][:2] == ["ruff.lint", "ruff.format"]
    assert all(item.mode == RunMode.APPLY for item in selected)


def test_check_bindings_do_not_replace_suite(catalog):
    project = ProjectConfig(
        suite="full",
        check_bindings=(
            CheckBinding(
                runnable="semgrep.scan",
                scope="semgrep",
            ),
        ),
    )
    suite_id, selected = resolve_runnables(
        mode=RunMode.CHECK,
        project=project,
        catalog=catalog,
    )
    assert suite_id == "full"
    assert "semgrep.scan" in [item.tool_id for item in selected]
    assert "radon.cc" in [item.tool_id for item in selected]


@pytest.mark.parametrize("suite_id", ["pre-commit", "standard", "python-quality"])
def test_commit_time_suites_run_checks_in_parallel(catalog, suite_id):
    parallel, _ = suite_execution_flags(catalog, suite_id, ProjectConfig(), RunMode.CHECK)
    assert parallel


def test_apply_mode_is_never_parallel_because_formatters_share_files(catalog):
    parallel, fail_fast = suite_execution_flags(
        catalog, "pre-commit", ProjectConfig(), RunMode.APPLY
    )
    assert not parallel
    assert fail_fast


def test_only_the_invoked_suites_flags_apply_to_nested_suites(catalog):
    # `policy` declares fail_fast, but inside `full` the outer suite's flags win.
    assert suite_execution_flags(catalog, "policy", ProjectConfig(), RunMode.CHECK)[1]
    assert not suite_execution_flags(catalog, "full", ProjectConfig(), RunMode.CHECK)[1]
