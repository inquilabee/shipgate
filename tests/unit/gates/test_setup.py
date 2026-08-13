from pathlib import Path

import pytest

from shipgate.catalog.loader import CatalogLoader
from shipgate.gates.setup import setup_bundled_gates
from shipgate.gates.setup.registry import make_setup
from shipgate.policy.core.path_allowlist import PathAllowlist


def test_setup_bundled_gates_scaffolds_allowlists(tmp_path: Path):
    setup_bundled_gates(tmp_path, CatalogLoader.load())
    allowlists = tmp_path / ".shipgate" / "allowlists"
    assert (allowlists / "module-private-vars.yaml").is_file()
    assert (allowlists / "acronyms.yaml").is_file()
    assert (allowlists / "folder-breadth.yaml").is_file()
    assert (allowlists / "module-size.yaml").is_file()
    assert (allowlists / "test-only-symbols.yaml").is_file()
    assert (allowlists / "repeated-strings.yaml").is_file()
    assert (allowlists / "class-local-functions.yaml").is_file()
    assert (allowlists / "staticmethod-soup.yaml").is_file()


def test_gate_setup_does_not_overwrite_existing_allowlist(tmp_path: Path):
    path = tmp_path / ".shipgate" / "allowlists" / "module-private-vars.yaml"
    path.parent.mkdir(parents=True)
    path.write_text(
        "entries:\n  - path: src/custom.py\n    reason: legacy exemption\n",
        encoding="utf-8",
    )
    make_setup("gate.module-private-vars")(tmp_path)
    assert "src/custom.py" in path.read_text(encoding="utf-8")


def test_path_allowlist_requires_reason(tmp_path: Path):
    path = tmp_path / "allowlist.yaml"
    path.write_text(
        "entries:\n  - path: src/foo.py\n",
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="requires reason"):
        PathAllowlist(path)


def test_path_allowlist_loads_entries(tmp_path: Path):
    path = tmp_path / "allowlist.yaml"
    path.write_text(
        "entries:\n  - path: src/foo.py\n    reason: pending refactor\n",
        encoding="utf-8",
    )
    allowlist = PathAllowlist(path)
    assert len(allowlist.entries) == 1
    assert allowlist.entries[0].path == "src/foo.py"
    assert allowlist.entries[0].reason == "pending refactor"
    assert allowlist.contains("src/foo.py")
