import dataclasses
from pathlib import Path

from shipgate.catalog.loader import CatalogLoader
from shipgate.domain.execution import ExecutionEnvironment, ResolvedRequest
from shipgate.domain.modes import RunMode
from shipgate.domain.options import NormalizedOptions
from shipgate.runtime.cache.check_cache import CheckResultCache
from shipgate.runtime.executor import CheckTimeoutError
from shipgate.runtime.session.check_runner import CheckRunner


def resolved_yamllint(tmp_path: Path, *, timeout_seconds: int | None) -> ResolvedRequest:
    (tmp_path / "cfg").mkdir()
    (tmp_path / "cfg" / "a.yaml").write_text("key: 1\n", encoding="utf-8")
    tool = dataclasses.replace(
        CatalogLoader.load().get_tool("yamllint.check"), timeout_seconds=timeout_seconds
    )
    return ResolvedRequest(
        runnable=tool.id,
        tool=tool,
        mode=RunMode.CHECK,
        options=NormalizedOptions(paths=(Path("cfg"),)),
        option_sources={},
        extra_args=(),
        project_root=tmp_path,
        output_path=tmp_path / ".shipgate" / "reports" / "raw" / f"{tool.id}.json",
        environment=ExecutionEnvironment(kind="system", root=None, env={}),
    )


class HangingExecutor:
    def __init__(self) -> None:
        self.limits: list[int | None] = []

    def run(self, argv, *, cwd, env=None, timeout_seconds=None):
        del cwd, env
        self.limits.append(timeout_seconds)
        raise CheckTimeoutError(argv, timeout_seconds or 600, stdout="partial out", stderr="slow")


def test_timeout_fails_only_that_check_and_is_not_cached(tmp_path: Path):
    resolved = resolved_yamllint(tmp_path, timeout_seconds=7)
    executor = HangingExecutor()
    runner = CheckRunner(catalog=CatalogLoader.load(), executor=executor, executor_is_default=False)

    report = runner.execute_check(resolved, "run-1")

    assert executor.limits == [7]
    assert (report.status, report.exit_code) == ("failed", 124)
    assert [f.rule_id for f in report.findings] == ["shipgate.timeout"]
    assert "timed out after 7s" in report.findings[0].message
    assert report.extra["timeout_seconds"] == 7
    assert report.stdout_path is not None
    assert (tmp_path / report.stdout_path).read_text(encoding="utf-8") == "partial out"
    assert CheckResultCache(tmp_path).lookup(resolved) is None
