from pathlib import Path

from shipgate.catalog.loader import load_catalog
from shipgate.gates.setup import setup_bundled_gates
from shipgate.gates.setup.registry import SETUPS


def test_setup_bundled_gates_scaffolds_allowlists(tmp_path: Path):
    setup_bundled_gates(tmp_path, load_catalog())
    allowlists = tmp_path / ".shipgate" / "allowlists"
    assert (allowlists / "module-private-vars.txt").is_file()
    assert (allowlists / "acronyms.yaml").is_file()
    assert (allowlists / "folder-breadth.txt").is_file()
    assert (allowlists / "module-size.txt").is_file()


def test_gate_setup_does_not_overwrite_existing_allowlist(tmp_path: Path):
    path = tmp_path / ".shipgate" / "allowlists" / "module-private-vars.txt"
    path.parent.mkdir(parents=True)
    path.write_text("src/custom.py\n", encoding="utf-8")
    SETUPS["gate.module-private-vars"](tmp_path)
    assert path.read_text(encoding="utf-8") == "src/custom.py\n"
