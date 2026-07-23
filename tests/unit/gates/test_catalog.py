from pathlib import Path

from shipgate.gates.core import GateCatalogMerger
from shipgate.gates.init import init_gate
from shipgate.paths import PROJECT_GATES_DIR


def test_init_gate_creates_script(tmp_path: Path):
    path = init_gate(tmp_path, "sample")
    assert path.is_file()
    assert path.suffix == ".sh"


def test_merge_gate_catalog(tmp_path: Path):
    gates_dir = tmp_path / PROJECT_GATES_DIR
    gates_dir.mkdir(parents=True)
    (gates_dir / "sample.sh").write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
    from shipgate.catalog.loader import CatalogLoader

    base = CatalogLoader.load()
    merged = GateCatalogMerger.merge(base, tmp_path)
    assert "gate.sample" in merged.tools
    assert merged.tools["gate.sample"].normalizer == "gate_json"
    assert merged.tools["gate.sample"].executable == "bash"
    assert "local-gates" in merged.suites
    assert GateCatalogMerger.discover(tmp_path)
