from pathlib import Path
from unittest.mock import MagicMock

import pytest

from shipgate.catalog.loader import load_catalog
from shipgate.errors import InstallError
from shipgate.runtime.environment import tools_manifest_path
from shipgate.runtime.install import (
    collect_install_requirements,
    install_suite,
    read_manifest,
)
from shipgate.runtime.installers.registry import INSTALLER_REGISTRY, get_installer


def test_install_plan_deduplicates_packages():
    catalog = load_catalog()
    python_packages, _binaries = collect_install_requirements("full", catalog)
    ruff_count = sum(1 for p in python_packages if p == "ruff")
    assert ruff_count == 1


def test_install_plan_collects_binaries():
    catalog = load_catalog()
    _python, binaries = collect_install_requirements("security", catalog)
    assert "gitleaks" in binaries


def test_install_plan_unions_format_suite_tools():
    catalog = load_catalog()
    python_packages, binaries = collect_install_requirements("full", catalog)
    assert "mdformat" in python_packages
    assert "shfmt" in binaries
    assert "yamlfmt" in binaries


def test_install_plan_includes_mdformat_frontmatter_requires():
    catalog = load_catalog()
    python_packages, _binaries = collect_install_requirements("format", catalog)
    install_def = python_packages["mdformat"]
    assert "mdformat-frontmatter>=2.0" in install_def.requires


def test_install_plan_format_suite_not_doubled():
    catalog = load_catalog()
    python_packages, binaries = collect_install_requirements("format", catalog)
    assert "mdformat" in python_packages
    assert "shfmt" in binaries
    assert "yamlfmt" in binaries
    assert sum(1 for pkg in python_packages if pkg == "ruff") == 1


def test_installer_registry_has_python_and_binary():
    assert "python" in INSTALLER_REGISTRY
    assert "binary" in INSTALLER_REGISTRY
    assert get_installer("python").manager == "python"
    assert get_installer("binary").manager == "binary"


def test_install_suite_writes_manifest_after_python_before_binaries(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    catalog = load_catalog()
    python_installer = MagicMock()
    binary_installer = MagicMock()
    binary_installer.install_packages.side_effect = InstallError("download failed")
    monkeypatch.setitem(INSTALLER_REGISTRY, "python", python_installer)
    monkeypatch.setitem(INSTALLER_REGISTRY, "binary", binary_installer)

    with pytest.raises(InstallError, match="binary install failed"):
        install_suite(tmp_path, "security", catalog)

    python_installer.install_packages.assert_called_once()
    manifest = read_manifest(tmp_path)
    assert manifest.get("packages")
    assert "gitleaks" not in manifest.get("binaries", {})
    assert tools_manifest_path(tmp_path).is_file()


def test_install_suite_records_successful_binaries_on_partial_failure(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    catalog = load_catalog()
    python_installer = MagicMock()
    binary_installer = MagicMock()

    def install_binary(project_root, packages):
        if "gitleaks" in packages:
            raise InstallError("gitleaks download failed")
        return None

    binary_installer.install_packages.side_effect = install_binary
    monkeypatch.setitem(INSTALLER_REGISTRY, "python", python_installer)
    monkeypatch.setitem(INSTALLER_REGISTRY, "binary", binary_installer)

    _python, binaries = collect_install_requirements("full", catalog)
    if len(binaries) < 2:
        pytest.skip("need multiple binaries to test partial install")

    with pytest.raises(InstallError, match="binary install failed"):
        install_suite(tmp_path, "full", catalog)

    manifest = read_manifest(tmp_path)
    assert manifest.get("packages")
    installed = set(manifest.get("binaries", {}))
    assert "gitleaks" not in installed
    assert len(installed) >= 1
