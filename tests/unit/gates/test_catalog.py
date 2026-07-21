from pathlib import Path

from shipgate.gates.catalog import discover_gates, merge_gate_catalog
from shipgate.gates.init import init_gate


def test_init_gate_creates_script(tmp_path: Path):
    path = init_gate(tmp_path, "sample")
    assert path.is_file()
    assert path.suffix == ".sh"


def test_merge_gate_catalog(tmp_path: Path):
    gates_dir = tmp_path / ".shipgate" / "gates"
    gates_dir.mkdir(parents=True)
    (gates_dir / "sample.sh").write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
    from shipgate.catalog.loader import load_catalog

    base = load_catalog()
    merged = merge_gate_catalog(base, tmp_path)
    assert "gate.sample" in merged.tools
    assert "local-gates" in merged.suites
    assert discover_gates(tmp_path)
