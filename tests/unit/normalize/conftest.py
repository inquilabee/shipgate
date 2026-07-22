"""Shared fixtures for normalizer tests."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from shipgate.domain.catalog import ToolDefinition
from shipgate.domain.execution import ExecutionEnvironment, ResolvedRequest
from shipgate.domain.modes import RunMode
from shipgate.domain.options import NormalizedOptions
from shipgate.runtime.executor import ProcessResult

if TYPE_CHECKING:
    from pathlib import Path

    from shipgate.domain.catalog import ToolDefinition as ToolDefinitionType


@pytest.fixture
def make_resolved_request(tmp_path: Path):
    def _make(
        *,
        tool: ToolDefinitionType | None = None,
        tool_id: str = "tool.check",
        executable: str = "tool",
        stdout_path: Path | None = None,
        options: NormalizedOptions | None = None,
    ) -> ResolvedRequest:
        output_path = stdout_path or tmp_path / "out.json"
        resolved_tool = tool or ToolDefinition(
            id=tool_id,
            executable=executable,
            modes=(RunMode.CHECK,),
        )
        return ResolvedRequest(
            runnable=resolved_tool.id,
            tool=resolved_tool,
            mode=RunMode.CHECK,
            options=options or NormalizedOptions(),
            option_sources={},
            extra_args=(),
            project_root=tmp_path,
            output_path=output_path,
            environment=ExecutionEnvironment(kind="system", root=None, env={}),
        )

    return _make


@pytest.fixture
def make_process_result(tmp_path: Path):
    def _make(
        *,
        stdout: str = "",
        stderr: str = "",
        exit_code: int = 0,
        cwd: Path | None = None,
    ) -> ProcessResult:
        return ProcessResult(
            argv=(),
            cwd=cwd or tmp_path,
            exit_code=exit_code,
            stdout=stdout,
            stderr=stderr,
            duration_ms=1,
        )

    return _make
