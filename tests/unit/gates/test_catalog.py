from pathlib import Path

import pytest

from shipgate.errors import ConfigError
from shipgate.gates.core import GateCatalogMerger
from shipgate.gates.init import init_gate
from shipgate.paths import PROJECT_GATES_DIR


def test_init_gate_creates_script(tmp_path: Path):
    path = init_gate(tmp_path, "sample")
    assert path.is_file()
    assert path.suffix == ".sh"


def test_init_gate_rejects_path_traversal(tmp_path: Path):
    with pytest.raises(ConfigError, match="invalid gate name"):
        init_gate(tmp_path, "../../tmp/evil")


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


def test_merge_updates_local_gates_when_suite_exists(tmp_path: Path):
    from shipgate.catalog.loader import CatalogLoader
    from shipgate.domain.catalog import Catalog, SuiteDefinition

    gates_dir = tmp_path / PROJECT_GATES_DIR
    gates_dir.mkdir(parents=True)
    (gates_dir / "alpha.sh").write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
    (gates_dir / "beta.sh").write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
    base = CatalogLoader.load()
    # Simulate a project overlay that already defined local-gates with one member.
    stale = Catalog(
        tools=base.tools,
        suites={
            **base.suites,
            "local-gates": SuiteDefinition(id="local-gates", members=("gate.alpha",)),
        },
        workflows=base.workflows,
        capabilities=base.capabilities,
    )
    merged = GateCatalogMerger.merge(stale, tmp_path)
    assert set(merged.suites["local-gates"].members) == {"gate.alpha", "gate.beta"}
    assert "gate.beta" in merged.tools
