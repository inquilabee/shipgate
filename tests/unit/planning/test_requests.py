import pytest
from shipgate.catalog.loader import load_catalog
from shipgate.domain.execution import ExecutionEnvironment
from shipgate.domain.modes import RunMode
from shipgate.domain.options import NormalizedOptions
from shipgate.errors import PlanningError
from shipgate.planning.requests import build_execution_request, resolve_request


def test_check_mode_rejects_fix(tmp_path):
    catalog = load_catalog()
    tool = catalog.get_tool("ruff.lint")
    request = build_execution_request(
        runnable="ruff.lint",
        mode=RunMode.CHECK,
        project_root=tmp_path,
        options=NormalizedOptions(fix=True),
    )
    env = ExecutionEnvironment(kind="system", root=None, env={})
    with pytest.raises(PlanningError):
        resolve_request(request, tool, env, target=tmp_path)


def test_default_output_path_recorded(tmp_path):
    catalog = load_catalog()
    tool = catalog.get_tool("ruff.lint")
    request = build_execution_request(
        runnable="ruff.lint",
        mode=RunMode.CHECK,
        project_root=tmp_path,
        options=NormalizedOptions(paths=(tmp_path,)),
    )
    env = ExecutionEnvironment(kind="system", root=None, env={})
    resolved = resolve_request(request, tool, env, target=tmp_path)
    assert "shipgate_default" in resolved.option_sources.values()
    assert resolved.output_path.name.endswith(".json")
