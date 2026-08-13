import io
import subprocess
import tarfile
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from shipgate.catalog.loader import CatalogLoader
from shipgate.domain.catalog import InstallDefinition
from shipgate.errors import InstallError
from shipgate.paths import PROJECT_MANAGED_PYTHON_ENV
from shipgate.runtime.environment import tools_manifest_path
from shipgate.runtime.install import (
    collect_install_requirements,
    install_suite,
    read_manifest,
)
from shipgate.runtime.installers.base import download_https_file, get_github_url
from shipgate.runtime.installers.binary_github import GitHubReleaseInstaller
from shipgate.runtime.installers.python import PythonInstaller
from shipgate.runtime.installers.registry import INSTALLER_REGISTRY, get_installer


def test_install_plan_deduplicates_packages():
    catalog = CatalogLoader.load()
    python_packages, _binaries = collect_install_requirements("full", catalog)
    ruff_count = sum(1 for p in python_packages if p == "ruff")
    assert ruff_count == 1


def test_install_plan_collects_binaries():
    catalog = CatalogLoader.load()
    _python, binaries = collect_install_requirements("security", catalog)
    assert "gitleaks" in binaries


def test_install_plan_unions_format_suite_tools():
    catalog = CatalogLoader.load()
    python_packages, binaries = collect_install_requirements("full", catalog)
    assert "mdformat" in python_packages
    assert "shfmt" in binaries
    assert "yamlfmt" in binaries


def test_install_plan_includes_mdformat_frontmatter_requires():
    catalog = CatalogLoader.load()
    python_packages, _binaries = collect_install_requirements("format", catalog)
    install_def = python_packages["mdformat"]
    assert "mdformat-frontmatter>=2.0" in install_def.requires


def test_install_plan_format_suite_not_doubled():
    catalog = CatalogLoader.load()
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
    catalog = CatalogLoader.load()
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
    catalog = CatalogLoader.load()
    python_installer = MagicMock()
    binary_installer = MagicMock()

    def install_binary(_project_root, packages, *, force=False):
        del force
        if "gitleaks" in packages:
            raise InstallError("gitleaks download failed")
        return

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


def test_install_suite_skips_requires_python_mismatch(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
):
    catalog = CatalogLoader.load()
    python_installer = MagicMock()
    binary_installer = MagicMock()
    monkeypatch.setitem(INSTALLER_REGISTRY, "python", python_installer)
    monkeypatch.setitem(INSTALLER_REGISTRY, "binary", binary_installer)
    monkeypatch.setattr("shipgate.runtime.install.host_python_minor", lambda: (3, 14))

    install_suite(tmp_path, "full", catalog)

    installed = python_installer.install_packages.call_args.args[1]
    assert "deadcode" not in installed
    assert "semgrep" not in installed
    assert "ruff" in installed
    captured = capsys.readouterr()
    assert "deadcode does not support Python 3.14" in captured.err
    assert "semgrep does not support Python 3.14" in captured.err


def test_binary_installer_rejects_escaped_name(tmp_path: Path):
    from shipgate.runtime.installers.binary import BinaryInstaller

    with pytest.raises(InstallError, match="escapes"):
        BinaryInstaller().install_packages(
            tmp_path,
            {
                "evil": InstallDefinition(
                    manager="binary",
                    package="../evil",
                    version="1.0.0",
                    binary="../evil",
                    allow_path=False,
                )
            },
        )


def test_python_installer_refuses_option_spec_and_uses_double_dash(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    pip_dir = tmp_path / PROJECT_MANAGED_PYTHON_ENV / "bin"
    pip_dir.mkdir(parents=True)
    (pip_dir / "pip").write_text("", encoding="utf-8")
    calls: list[list[str]] = []

    def fake_run(argv, **_kwargs):
        calls.append(list(argv))

        class Result:
            returncode = 0
            stderr = ""

        return Result()

    monkeypatch.setattr("shipgate.runtime.installers.python.run_command", fake_run)
    installer = PythonInstaller()
    installer.install_packages(
        tmp_path,
        {"ruff": InstallDefinition(manager="python", package="ruff", version="0.15.22")},
    )
    assert calls
    assert calls[0][1:3] == ["install", "--"]
    assert calls[0][-1] == "ruff==0.15.22"

    with pytest.raises(InstallError, match="pip option"):
        installer.install_packages(
            tmp_path,
            {
                "evil": InstallDefinition(
                    manager="python",
                    package="--index-url",
                    version="1.0.0",
                )
            },
        )


def write_tar_xz(path: Path, binary_name: str, payload: bytes) -> None:
    buffer = io.BytesIO()
    info = tarfile.TarInfo(name=binary_name)
    info.size = len(payload)
    with tarfile.open(fileobj=buffer, mode="w:xz") as archive:
        archive.addfile(info, io.BytesIO(payload))
    path.write_bytes(buffer.getvalue())


def test_extract_binary_reads_tar_xz(tmp_path: Path) -> None:
    archive_path = tmp_path / "shellcheck-0.11.0-linux.x86_64.tar.xz"
    write_tar_xz(archive_path, "shellcheck", b"#!/bin/sh\n")
    extracted = GitHubReleaseInstaller().extract_binary(archive_path, "shellcheck")
    assert extracted.read_bytes() == b"#!/bin/sh\n"
    assert extracted.name == "shellcheck"


def test_extract_from_tar_maps_errors_to_install_error(tmp_path: Path) -> None:
    archive_path = tmp_path / "broken.tar.xz"
    archive_path.write_bytes(b"not an xz tar")
    with pytest.raises(InstallError, match="failed to extract shellcheck"):
        GitHubReleaseInstaller().extract_from_tar(archive_path, "shellcheck", xz=True)


def test_venv_called_process_error_is_install_error(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fake_run(*args, **kwargs):
        del args, kwargs
        raise subprocess.CalledProcessError(1, ["python", "-m", "venv"])

    monkeypatch.setattr("shipgate.runtime.installers.python.run_command", fake_run)
    with pytest.raises(InstallError, match="failed to create venv"):
        PythonInstaller().install_packages(
            tmp_path,
            {"ruff": InstallDefinition(manager="python", package="ruff", version="0.15.22")},
        )


def test_get_github_url_refuses_offsite_redirect(monkeypatch: pytest.MonkeyPatch) -> None:
    response = MagicMock()
    response.url = "https://evil.example/payload"
    response.raise_for_status.return_value = None

    def fake_get(*args, **kwargs):
        del args, kwargs
        return response

    monkeypatch.setattr("shipgate.runtime.installers.base.requests.get", fake_get)
    with pytest.raises(InstallError, match="refusing redirect off github"):
        get_github_url("https://github.com/owner/repo/releases/download/x", timeout=1)


def test_download_https_file_refuses_non_github(tmp_path: Path) -> None:
    with pytest.raises(InstallError, match="refusing untrusted download URL"):
        download_https_file("https://evil.example/x", tmp_path / "out.bin")
