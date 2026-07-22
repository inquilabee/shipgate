"""Gate catalog helpers."""

from __future__ import annotations

from typing import TYPE_CHECKING

from shipgate.domain.catalog import Catalog, SuiteDefinition, ToolDefinition
from shipgate.domain.modes import RunMode

if TYPE_CHECKING:
    from pathlib import Path


def discover_gates(project_root: Path) -> list[Path]:
    gates_dir = project_root / ".shipgate" / "gates"
    if not gates_dir.is_dir():
        return []
    return sorted(p for p in gates_dir.glob("*.sh") if p.is_file())


def merge_gate_catalog(base: Catalog, project_root: Path) -> Catalog:
    gates = discover_gates(project_root)
    if not gates:
        return base
    tools = dict(base.tools)
    suites = dict(base.suites)
    gate_members: list[str] = []
    for gate_path in gates:
        gate_id = f"gate.{gate_path.stem}"
        gate_members.append(gate_id)
        tools[gate_id] = ToolDefinition(
            id=gate_id,
            executable="bash",
            script=str(gate_path.resolve()),
            subcommand=(),
            cli={},
            capabilities=("Gates",),
            normalizer="gate_json",
            modes=(RunMode.CHECK, RunMode.APPLY),
            option_order=(),
        )
    if "local-gates" not in suites:
        suites["local-gates"] = SuiteDefinition(
            id="local-gates",
            members=tuple(gate_members),
            parallel=False,
            fail_fast=True,
        )
    return Catalog(
        tools=tools,
        suites=suites,
        workflows=base.workflows,
        capabilities=base.capabilities,
    )
