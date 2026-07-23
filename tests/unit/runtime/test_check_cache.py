from pathlib import Path

from shipgate.catalog.loader import load_catalog
from shipgate.domain.execution import ExecutionEnvironment, ResolvedRequest
from shipgate.domain.modes import RunMode
from shipgate.domain.options import NormalizedOptions
from shipgate.domain.reports import CheckReport
from shipgate.runtime.check_cache import CheckResultCache


def make_resolved_request(
    tmp_path: Path,
    tool_id: str,
    *,
    paths: tuple[Path, ...],
) -> ResolvedRequest:
    tool = load_catalog().get_tool(tool_id)
    return ResolvedRequest(
        runnable=tool.id,
        tool=tool,
        mode=RunMode.CHECK,
        options=NormalizedOptions(paths=paths),
        option_sources={},
        extra_args=(),
        project_root=tmp_path,
        output_path=tmp_path / ".shipgate" / "reports" / "raw" / f"{tool.id}.json",
        environment=ExecutionEnvironment(kind="system", root=None, env={}),
    )


def test_check_result_cache_round_trip(tmp_path: Path):
    resolved = make_resolved_request(tmp_path, "yamllint.check", paths=(Path("cfg.yaml"),))
    cache = CheckResultCache(tmp_path)
    report = CheckReport(
        check_id=resolved.tool.id,
        tool_id=resolved.tool.id,
        status="passed",
        exit_code=0,
    )
    cache.store(resolved, report)
    loaded = cache.lookup(resolved)
    assert loaded is not None
    assert loaded.status == "passed"
    assert loaded.tool_id == resolved.tool.id


def test_check_result_cache_skips_root_delivery_tools(tmp_path: Path):
    resolved = make_resolved_request(tmp_path, "ruff.lint", paths=(Path(),))
    cache = CheckResultCache(tmp_path)
    report = CheckReport(
        check_id=resolved.tool.id,
        tool_id=resolved.tool.id,
        status="passed",
        exit_code=0,
    )
    cache.store(resolved, report)
    assert cache.lookup(resolved) is None


def test_check_result_cache_skips_gate_tools(tmp_path: Path):
    resolved = make_resolved_request(
        tmp_path,
        "gate.module-private-vars",
        paths=(Path("src"),),
    )
    cache = CheckResultCache(tmp_path)
    report = CheckReport(
        check_id=resolved.tool.id,
        tool_id=resolved.tool.id,
        status="passed",
        exit_code=0,
    )
    cache.store(resolved, report)
    assert cache.lookup(resolved) is None


def test_check_result_cache_respects_disabled_flag(tmp_path: Path):
    resolved = make_resolved_request(tmp_path, "yamllint.check", paths=(Path("cfg.yaml"),))
    cache = CheckResultCache(tmp_path, disabled=True)
    report = CheckReport(
        check_id=resolved.tool.id,
        tool_id=resolved.tool.id,
        status="passed",
        exit_code=0,
    )
    cache.store(resolved, report)
    assert cache.lookup(resolved) is None
