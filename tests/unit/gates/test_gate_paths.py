from pathlib import Path

import pytest

from shipgate.domain.catalog import ToolDefinition
from shipgate.domain.modes import RunMode
from shipgate.errors import PlanningError
from shipgate.gates.core.catalog import GateCatalogMerger
from shipgate.gates.paths import resolve_gate_script


def test_resolve_gate_script_rejects_absolute_outside_allowlist(tmp_path: Path):
    evil = tmp_path / "evil.sh"
    evil.write_text("#!/bin/bash\n", encoding="utf-8")
    tool = ToolDefinition(
        id="gate.evil",
        executable="bash",
        script=str(evil),
        capabilities=("Gates",),
        modes=(RunMode.CHECK,),
    )
    with pytest.raises(PlanningError, match="not allowed"):
        resolve_gate_script(tool, tmp_path / "project")


def test_discover_gates_ignores_non_files_and_stays_in_dir(tmp_path: Path):
    gates = tmp_path / ".shipgate" / "gates"
    gates.mkdir(parents=True)
    good = gates / "ok.sh"
    good.write_text("#!/bin/bash\n", encoding="utf-8")
    (gates / "subdir").mkdir()
    paths = GateCatalogMerger.discover(tmp_path)
    assert paths == [good.resolve()]
