"""Finalize tool argv with resolved executable (Adapter layer)."""

from __future__ import annotations

from typing import TYPE_CHECKING

from shipgate.adapter.argv import build_argv

if TYPE_CHECKING:
    from shipgate.domain.execution import ResolvedRequest


def build_tool_argv(resolved: ResolvedRequest, *, executable: str) -> tuple[str, ...]:
    argv_list = list(build_argv(resolved))
    argv_list[0] = executable
    return tuple(argv_list)
