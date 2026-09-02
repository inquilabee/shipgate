from pathlib import Path
from unittest.mock import MagicMock

import pytest

from shipgate.catalog.loader import CatalogLoader
from shipgate.domain.catalog import InstallDefinition
from shipgate.paths import PROJECT_MANAGED_BIN_DIR, PROJECT_MANAGED_PYTHON_ENV
from shipgate.runtime.environment import tools_manifest_path
from shipgate.runtime.install import (
    collect_install_requirements,
    install_suite,
    partition_python_packages,
)
from shipgate.runtime.installers.registry import INSTALLER_REGISTRY
from shipgate.runtime.tool_manifest import ManagedToolState, write_manifest


def python_install_def(name: str, version: str) -> InstallDefinition:
    return InstallDefinition(manager="python", package=name, version=version)


def binary_install_def(name: str, version: str) -> InstallDefinition:
    return InstallDefinition(manager="binary", package=name, version=version, binary=name)


def seed_managed_state(
    project_root: Path,
    *,
    python_packages: dict[str, InstallDefinition],
    binary_packages: dict[str, InstallDefinition],
) -> None:
    (project_root / PROJECT_MANAGED_PYTHON_ENV).mkdir(parents=True, exist_ok=True)
    bin_dir = project_root / PROJECT_MANAGED_BIN_DIR
    bin_dir.mkdir(parents=True, exist_ok=True)
    for install_def in binary_packages.values():
        (bin_dir / (install_def.binary or install_def.package)).write_text("", encoding="utf-8")
    write_manifest(project_root, python_packages=python_packages, binary_packages=binary_packages)


def seed_security_suite(project_root: Path) -> None:
    catalog = CatalogLoader.load()
    python_packages, binary_packages = collect_install_requirements("security", catalog)
    python_packages, _skipped = partition_python_packages(python_packages)
    seed_managed_state(
        project_root,
        python_packages=python_packages,
        binary_packages=binary_packages,
    )


def test_satisfied_when_manifest_matches(tmp_path: Path):
    python_packages = {"ruff": python_install_def("ruff", "0.15.22")}
    binary_packages = {"gitleaks": binary_install_def("gitleaks", "8.30.1")}
    seed_managed_state(tmp_path, python_packages=python_packages, binary_packages=binary_packages)
    assert ManagedToolState(tmp_path).satisfies(python_packages, binary_packages) is True


def test_stale_extra_manifest_entry_does_not_block(tmp_path: Path):
    ruff = {"ruff": python_install_def("ruff", "0.15.22")}
    seed_managed_state(
        tmp_path,
        python_packages={**ruff, "ty": python_install_def("ty", "1")},
        binary_packages={},
    )
    assert ManagedToolState(tmp_path).satisfies(ruff, {}) is True


def test_unsatisfied_on_version_drift(tmp_path: Path):
    seed_managed_state(
        tmp_path,
        python_packages={"ruff": python_install_def("ruff", "0.15.22")},
        binary_packages={},
    )
    drifted = {"ruff": python_install_def("ruff", "0.16.0")}
    assert ManagedToolState(tmp_path).satisfies(drifted, {}) is False


def test_unsatisfied_without_managed_venv(tmp_path: Path):
    packages = {"ruff": python_install_def("ruff", "0.15.22")}
    tools_manifest_path(tmp_path).parent.mkdir(parents=True, exist_ok=True)
    write_manifest(tmp_path, python_packages=packages, binary_packages={})
    assert ManagedToolState(tmp_path).satisfies(packages, {}) is False


def test_unsatisfied_when_binary_missing_from_bin_dir(tmp_path: Path):
    binary_packages = {"gitleaks": binary_install_def("gitleaks", "8.30.1")}
    seed_managed_state(tmp_path, python_packages={}, binary_packages=binary_packages)
    (tmp_path / PROJECT_MANAGED_BIN_DIR / "gitleaks").unlink()
    assert ManagedToolState(tmp_path).satisfies({}, binary_packages) is False


def test_install_suite_skips_installers_when_satisfied(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
):
    seed_security_suite(tmp_path)
    python_installer = MagicMock()
    binary_installer = MagicMock()
    monkeypatch.setitem(INSTALLER_REGISTRY, "python", python_installer)
    monkeypatch.setitem(INSTALLER_REGISTRY, "binary", binary_installer)

    result = install_suite(tmp_path, "security", CatalogLoader.load())

    python_installer.install_packages.assert_not_called()
    binary_installer.install_packages.assert_not_called()
    assert result == tools_manifest_path(tmp_path)
    assert "already satisfied" in capsys.readouterr().err


def test_install_suite_force_reinstalls_when_satisfied(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    seed_security_suite(tmp_path)
    python_installer = MagicMock()
    monkeypatch.setitem(INSTALLER_REGISTRY, "python", python_installer)
    monkeypatch.setitem(INSTALLER_REGISTRY, "binary", MagicMock())

    install_suite(tmp_path, "security", CatalogLoader.load(), force=True)

    python_installer.install_packages.assert_called_once()
