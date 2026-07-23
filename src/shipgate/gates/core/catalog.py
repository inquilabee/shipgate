"""Merge project-local gate scripts into a catalog."""

from __future__ import annotations

from typing import TYPE_CHECKING

from shipgate.domain.catalog import Catalog, SuiteDefinition, ToolDefinition
from shipgate.domain.modes import RunMode
from shipgate.paths import PROJECT_GATES_DIR

if TYPE_CHECKING:
    from pathlib import Path


class GateCatalogMerger:
    """Discover project-local gate scripts and overlay them onto a bundled catalog."""

    def __init__(self, *, project_root: Path) -> None:
        self._project_root = project_root

    @classmethod
    def merge(cls, base: Catalog, project_root: Path) -> Catalog:
        return cls(project_root=project_root)._merge(base)

    @classmethod
    def discover(cls, project_root: Path) -> list[Path]:
        return cls._discover_gate_scripts(project_root)

    def _merge(self, base: Catalog) -> Catalog:
        gates = self._discover_gate_scripts(self._project_root)
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

    @staticmethod
    def _discover_gate_scripts(project_root: Path) -> list[Path]:
        gates_dir = project_root / PROJECT_GATES_DIR
        if not gates_dir.is_dir():
            return []
        return sorted(p for p in gates_dir.glob("*.sh") if p.is_file())
