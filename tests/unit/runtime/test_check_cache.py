from pathlib import Path

from shipgate.catalog.loader import CatalogLoader
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
    tool = CatalogLoader.load().get_tool(tool_id)
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


def test_check_result_cache_includes_version_in_key(tmp_path: Path):
    from dataclasses import replace

    base = make_resolved_request(tmp_path, "yamllint.check", paths=(Path("cfg.yaml"),))
    assert base.tool.install is not None
    tool_v1 = replace(
        base.tool,
        install=replace(base.tool.install, version="1.0.0"),
    )
    tool_v2 = replace(
        base.tool,
        install=replace(base.tool.install, version="2.0.0"),
    )
    resolved_v1 = replace(base, tool=tool_v1)
    resolved_v2 = replace(base, tool=tool_v2)
    cache = CheckResultCache(tmp_path)
    report = CheckReport(
        check_id=base.tool.id,
        tool_id=base.tool.id,
        status="passed",
        exit_code=0,
    )
    cache.store(resolved_v1, report)
    assert cache.lookup(resolved_v1) is not None
    assert cache.lookup(resolved_v2) is None


def test_check_result_cache_honors_ttl(tmp_path: Path, monkeypatch):
    from dataclasses import replace

    from shipgate.domain.catalog import CacheDefinition

    base = make_resolved_request(tmp_path, "yamllint.check", paths=(Path("cfg.yaml"),))
    tool = replace(base.tool, cache=CacheDefinition(results=True, ttl_seconds=10))
    resolved = replace(base, tool=tool)
    cache = CheckResultCache(tmp_path)
    report = CheckReport(
        check_id=resolved.tool.id,
        tool_id=resolved.tool.id,
        status="passed",
        exit_code=0,
    )
    cache.store(resolved, report)
    monkeypatch.setattr(
        CheckResultCache,
        "_is_expired",
        staticmethod(lambda _path, _resolved: True),
    )
    assert cache.lookup(resolved) is None


def test_check_result_cache_results_false(tmp_path: Path):
    from dataclasses import replace

    from shipgate.domain.catalog import CacheDefinition

    base = make_resolved_request(tmp_path, "yamllint.check", paths=(Path("cfg.yaml"),))
    tool = replace(base.tool, cache=CacheDefinition(results=False))
    resolved = replace(base, tool=tool)
    cache = CheckResultCache(tmp_path)
    report = CheckReport(
        check_id=resolved.tool.id,
        tool_id=resolved.tool.id,
        status="passed",
        exit_code=0,
    )
    cache.store(resolved, report)
    assert cache.lookup(resolved) is None
