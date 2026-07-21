"""Execution request domain types."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path

from shipgate.domain.catalog import ToolDefinition
from shipgate.domain.modes import RunMode
from shipgate.domain.options import NormalizedOptions


@dataclass(frozen=True)
class ExecutionEnvironment:
    kind: str
    root: Path | None
    env: Mapping[str, str]


@dataclass(frozen=True)
class ExecutionRequest:
    runnable: str
    mode: RunMode
    options: NormalizedOptions
    extra_args: tuple[str, ...]
    project_root: Path


@dataclass(frozen=True)
class ResolvedRequest:
    runnable: str
    tool: ToolDefinition
    mode: RunMode
    options: NormalizedOptions
    option_sources: Mapping[str, str]
    extra_args: tuple[str, ...]
    project_root: Path
    output_path: Path
    environment: ExecutionEnvironment
