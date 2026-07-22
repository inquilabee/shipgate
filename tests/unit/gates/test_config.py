from pathlib import Path

from shipgate.catalog.loader import load_catalog
from shipgate.domain.project import ProjectConfig
from shipgate.gates.config import apply_project_allowlist, load_gate_config


def test_apply_project_allowlist_overrides_gate_config():
    project = ProjectConfig(
        allowlists={"gate.module-size": "custom/allowlist.txt"},
    )
    config = apply_project_allowlist(
        project,
        "gate.module-size",
        {"allowlist_file": ".shipgate/allowlists/module-size.txt"},
    )
    assert config["allowlist_file"] == "custom/allowlist.txt"


def test_apply_project_allowlist_ignores_other_gates():
    project = ProjectConfig(
        allowlists={"gate.module-size": "custom/allowlist.txt"},
    )
    config = apply_project_allowlist(
        project,
        "gate.folder-breadth",
        {"allowlist_file": ".shipgate/allowlists/folder-breadth.txt"},
    )
    assert config["allowlist_file"] == ".shipgate/allowlists/folder-breadth.txt"


def test_load_gate_config_applies_project_allowlist(tmp_path: Path):
    gate_dir = tmp_path / ".shipgate" / "configs" / "gates"
    gate_dir.mkdir(parents=True)
    (gate_dir / "gate.module-size.yaml").write_text(
        "allowlist_file: .shipgate/allowlists/module-size.txt\n",
        encoding="utf-8",
    )
    custom = tmp_path / "custom-allowlist.txt"
    custom.write_text("# custom\n", encoding="utf-8")
    project = ProjectConfig(
        allowlists={"gate.module-size": "custom-allowlist.txt"},
    )
    tool = load_catalog().get_tool("gate.module-size")
    config = load_gate_config(tool, tmp_path, project, config_paths=())
    assert config["allowlist_file"] == str(custom.resolve())


def test_load_gate_config_allowlist_without_gate_yaml(tmp_path: Path):
    custom = tmp_path / "custom-allowlist.txt"
    custom.write_text("# custom\n", encoding="utf-8")
    project = ProjectConfig(
        allowlists={"gate.module-size": "custom-allowlist.txt"},
    )
    tool = load_catalog().get_tool("gate.module-size")
    config = load_gate_config(tool, tmp_path, project, config_paths=())
    assert config["allowlist_file"] == str(custom.resolve())
