"""Tests for catalog tool inheritance."""

from pathlib import Path

import pytest

from shipgate.catalog.core.tool_extends import ToolExtendsResolver
from shipgate.catalog.loader import CatalogLoader
from shipgate.errors import CatalogError
from shipgate.runtime.install import collect_install_requirements


def test_child_inherits_parent_and_overrides_threshold():
    bundled = {
        "base.tool": {
            "executable": "tool",
            "modes": ["check"],
            "cli": {
                "threshold": {"flag": "--threshold", "style": "scalar", "default": "5"},
            },
            "install": {"manager": "binary", "package": "tool", "binary": "tool"},
        },
        "child.tool": {
            "extends": "base.tool",
            "cli": {"threshold": {"default": "2"}},
            "scope": {"extensions": [".py"]},
        },
    }
    resolved = ToolExtendsResolver.resolve(bundled)
    child = resolved["child.tool"]
    assert child["executable"] == "tool"
    assert child["install"]["binary"] == "tool"
    assert child["cli"]["threshold"]["default"] == "2"
    assert child["cli"]["threshold"]["flag"] == "--threshold"
    assert child["scope"]["extensions"] == [".py"]
    assert "extends" not in child


def test_multi_hop_inheritance():
    bundled = {
        "a.tool": {"executable": "a", "modes": ["check"], "capabilities": ["Quality"]},
        "b.tool": {"extends": "a.tool", "cli": {"paths": {"style": "positional"}}},
        "c.tool": {"extends": "b.tool", "normalizer": "ruff"},
    }
    resolved = ToolExtendsResolver.resolve(bundled)
    assert resolved["c.tool"]["executable"] == "a"
    assert resolved["c.tool"]["capabilities"] == ["Quality"]
    assert resolved["c.tool"]["cli"]["paths"]["style"] == "positional"
    assert resolved["c.tool"]["normalizer"] == "ruff"


def test_project_child_extends_bundled_parent(tmp_path: Path):
    tools_dir = tmp_path / ".shipgate/catalog/tools"
    tools_dir.mkdir(parents=True)
    (tools_dir / "custom.variant.yaml").write_text(
        "custom.variant:\n  extends: ruff.lint\n  cli:\n    threshold:\n      default: '1'\n",
        encoding="utf-8",
    )
    catalog = CatalogLoader.load(project_root=tmp_path)
    variant = catalog.get_tool("custom.variant")
    parent = catalog.get_tool("ruff.lint")
    assert variant.executable == parent.executable
    assert variant.cli["threshold"].default == "1"
    assert variant.cli["paths"].style == parent.cli["paths"].style


def test_same_id_project_extends_bundled_parent(tmp_path: Path):
    tools_dir = tmp_path / ".shipgate/catalog/tools"
    tools_dir.mkdir(parents=True)
    (tools_dir / "ruff.lint.yaml").write_text(
        "ruff.lint:\n  extends: ruff.lint\n  executable: custom-ruff\n",
        encoding="utf-8",
    )
    catalog = CatalogLoader.load(project_root=tmp_path)
    tool = catalog.get_tool("ruff.lint")
    assert tool.executable == "custom-ruff"
    assert tool.cli["paths"].style == "positional"


def test_project_without_extends_replaces_bundled_tool(tmp_path: Path):
    tools_dir = tmp_path / ".shipgate/catalog/tools"
    tools_dir.mkdir(parents=True)
    (tools_dir / "ruff.lint.yaml").write_text(
        "ruff.lint:\n  executable: custom-ruff\n  modes:\n    - check\n",
        encoding="utf-8",
    )
    catalog = CatalogLoader.load(project_root=tmp_path)
    tool = catalog.get_tool("ruff.lint")
    assert tool.executable == "custom-ruff"
    assert tool.cli == {}


def test_missing_parent_raises():
    bundled = {"child.tool": {"extends": "missing.tool", "executable": "child"}}
    with pytest.raises(CatalogError, match="extends unknown parent"):
        ToolExtendsResolver.resolve(bundled)


def test_invalid_extends_type_raises():
    bundled = {"child.tool": {"extends": 42, "executable": "child"}}
    with pytest.raises(CatalogError, match="extends must be a tool id string"):
        ToolExtendsResolver.resolve(bundled)


def test_cycle_raises():
    bundled = {
        "a.tool": {"extends": "b.tool", "executable": "a"},
        "b.tool": {"extends": "a.tool", "executable": "b"},
    }
    with pytest.raises(CatalogError, match="inheritance cycle"):
        ToolExtendsResolver.resolve(bundled)


def test_bundled_jscpd_variants_share_install_and_differ_by_scope():
    catalog = CatalogLoader.load()
    python = catalog.get_tool("jscpd.check.python")
    other = catalog.get_tool("jscpd.check.other")
    assert python.executable == other.executable
    assert python.install == other.install
    assert python.cli["threshold"].default == "2"
    assert other.cli["threshold"].default == "5"
    assert python.scope.extensions == (".py",)
    assert other.scope.extensions == ()
    assert python.configuration.bundled == "configs/jscpd.python.json"
    assert other.configuration.bundled == "configs/jscpd.other.json"


def test_extended_suite_installs_jscpd_once():
    catalog = CatalogLoader.load()
    _python, binaries = collect_install_requirements("extended", catalog)
    assert "jscpd" in binaries
    assert sum(1 for name in binaries if name == "jscpd") == 1
