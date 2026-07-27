"""Shared fixtures for radon normalizer tests."""

from pathlib import Path

from shipgate.domain.catalog import ToolDefinition
from shipgate.domain.execution import ExecutionEnvironment, ResolvedRequest
from shipgate.domain.modes import RunMode
from shipgate.domain.options import NormalizedOptions
from shipgate.domain.reports import CheckReport
from shipgate.normalize.radon import RadonNormalizer
from shipgate.runtime.executor import ProcessResult


def resolved(
    tmp_path: Path,
    tool_id: str,
    subcommand: tuple[str, ...],
    *,
    threshold: str | None = None,
    extra: dict[str, object] | None = None,
) -> ResolvedRequest:
    tool = ToolDefinition(
        id=tool_id,
        executable="radon",
        subcommand=subcommand,
        normalizer="radon",
    )
    return ResolvedRequest(
        runnable=tool_id,
        tool=tool,
        mode=RunMode.CHECK,
        options=NormalizedOptions(
            paths=(tmp_path,),
            threshold=threshold,
            extra=dict(extra or {}),
        ),
        option_sources={},
        extra_args=(),
        project_root=tmp_path,
        output_path=tmp_path / "out.json",
        environment=ExecutionEnvironment(kind="system", root=None, env={}),
    )


def normalize_payload(
    tmp_path: Path,
    tool_id: str,
    subcommand: tuple[str, ...],
    payload: str,
    *,
    threshold: str | None = None,
    extra: dict[str, object] | None = None,
) -> CheckReport:
    return RadonNormalizer().normalize(
        resolved(tmp_path, tool_id, subcommand, threshold=threshold, extra=extra),
        ProcessResult(
            argv=(),
            cwd=tmp_path,
            exit_code=0,
            stdout=payload,
            stderr="",
            duration_ms=1,
        ),
    )
