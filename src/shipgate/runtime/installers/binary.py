"""Binary tool installers."""

from __future__ import annotations

import os
import platform
import shutil
import subprocess
import sys
import tarfile
import tempfile
import zipfile
from pathlib import Path
from typing import TYPE_CHECKING, Protocol

from shipgate.errors import InstallError
from shipgate.paths import managed_bin_dir
from shipgate.runtime.installers.base import download_https_file, link_binary

if TYPE_CHECKING:
    from shipgate.domain.catalog import InstallDefinition

BINARY_RELEASES: dict[str, dict[str, str]] = {
    "gitleaks": {
        "repo": "gitleaks/gitleaks",
        "asset_template": "gitleaks_{version}_{os}_{arch}.tar.gz",
        "binary_name": "gitleaks",
    },
    "shfmt": {
        "repo": "mvdan/sh",
        "asset_template": "shfmt_{version}_{os}_{arch}",
        "binary_name": "shfmt",
    },
    "shellcheck": {
        "repo": "koalaman/shellcheck",
        "asset_template": "shellcheck-{version}-{os}.{arch}.tar.xz",
        "binary_name": "shellcheck",
    },
}


class BinaryInstallStrategy(Protocol):
    def can_install(self, binary_name: str, install_def: InstallDefinition) -> bool: ...

    def install(
        self,
        bin_dir: Path,
        binary_name: str,
        install_def: InstallDefinition,
        destination: Path,
    ) -> None: ...


class PathBinaryInstaller:
    def can_install(self, binary_name: str, install_def: InstallDefinition) -> bool:
        return shutil.which(binary_name) is not None

    def install(
        self,
        bin_dir: Path,
        binary_name: str,
        install_def: InstallDefinition,
        destination: Path,
    ) -> None:
        existing = shutil.which(binary_name)
        if existing is None:
            raise InstallError(f"binary {binary_name!r} is not available on PATH")
        link_binary(Path(existing), destination)


class GitHubReleaseInstaller:
    def can_install(self, binary_name: str, install_def: InstallDefinition) -> bool:
        return binary_name in BINARY_RELEASES

    def install(
        self,
        bin_dir: Path,
        binary_name: str,
        install_def: InstallDefinition,
        destination: Path,
    ) -> None:
        release = BINARY_RELEASES[binary_name]
        version = normalize_version(install_def.version or "latest")
        asset_name = release["asset_template"].format(
            version=version.lstrip("v"),
            os=github_os(),
            arch=github_arch(),
        )
        if version == "latest":
            url = (
                f"https://github.com/{release['repo']}/releases/latest/download/{asset_name}"
            )
        else:
            url = (
                f"https://github.com/{release['repo']}/releases/download/"
                f"{version}/{asset_name}"
            )
        with tempfile.TemporaryDirectory() as tmp:
            archive_path = Path(tmp) / asset_name
            try:
                download_https_file(url, archive_path)
            except OSError as exc:
                raise InstallError(f"failed to download {binary_name}: {exc}") from exc
            extracted = extract_binary(archive_path, release["binary_name"])
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(extracted, destination)
            destination.chmod(destination.stat().st_mode | 0o100)


class NpmInstaller:
    def can_install(self, binary_name: str, install_def: InstallDefinition) -> bool:
        return binary_name == "markdownlint"

    def install(
        self,
        bin_dir: Path,
        binary_name: str,
        install_def: InstallDefinition,
        destination: Path,
    ) -> None:
        npm = shutil.which("npm")
        if npm is None:
            raise InstallError("npm is required to install markdownlint-cli")
        result = subprocess.run(  # noqa: S603
            [npm, "install", "--prefix", str(bin_dir), "markdownlint-cli"],
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode != 0:
            raise InstallError(f"failed to install markdownlint-cli: {result.stderr.strip()}")
        installed = bin_dir / "node_modules" / ".bin" / "markdownlint"
        if sys.platform == "win32":
            installed = installed.with_suffix(".cmd")
        if not installed.is_file():
            raise InstallError("markdownlint-cli install did not produce an executable")
        link_binary(installed, destination)


class GoInstaller:
    def can_install(self, binary_name: str, install_def: InstallDefinition) -> bool:
        return binary_name == "yamlfmt"

    def install(
        self,
        bin_dir: Path,
        binary_name: str,
        install_def: InstallDefinition,
        destination: Path,
    ) -> None:
        go = shutil.which("go")
        if go is None:
            raise InstallError("go is required to install yamlfmt")
        result = subprocess.run(  # noqa: S603
            [go, "install", "github.com/google/yamlfmt/cmd/yamlfmt@latest"],
            capture_output=True,
            text=True,
            env={**os.environ, "GOBIN": str(bin_dir)},
            check=False,
        )
        if result.returncode != 0:
            raise InstallError(f"failed to install yamlfmt: {result.stderr.strip()}")
        if not destination.is_file():
            raise InstallError("yamlfmt install did not produce an executable")


class BinaryInstaller:
    manager = "binary"

    def __init__(self, strategies: tuple[BinaryInstallStrategy, ...] | None = None) -> None:
        self._strategies = strategies or (
            PathBinaryInstaller(),
            GitHubReleaseInstaller(),
            NpmInstaller(),
            GoInstaller(),
        )

    def install_packages(
        self,
        project_root: Path,
        packages: dict[str, InstallDefinition],
    ) -> None:
        bin_dir = managed_bin_dir(project_root)
        bin_dir.mkdir(parents=True, exist_ok=True)
        for _name, install_def in sorted(packages.items()):
            binary_name = install_def.binary or install_def.package
            destination = bin_dir / binary_name
            if sys.platform == "win32":
                destination = destination.with_suffix(".exe")
            if destination.is_file():
                continue
            strategy = self._resolve_strategy(binary_name, install_def)
            strategy.install(bin_dir, binary_name, install_def, destination)

    def _resolve_strategy(
        self,
        binary_name: str,
        install_def: InstallDefinition,
    ) -> BinaryInstallStrategy:
        for strategy in self._strategies:
            if strategy.can_install(binary_name, install_def):
                return strategy
        raise InstallError(
            f"binary {binary_name!r} is not available on PATH and has no managed installer",
            hint="install the tool manually or add it to PATH",
        )


def normalize_version(version: str) -> str:
    cleaned = version.strip()
    if cleaned.startswith(">="):
        return "latest"
    return cleaned


def extract_binary(archive_path: Path, binary_name: str) -> Path:
    suffixes = "".join(archive_path.suffixes)
    if suffixes.endswith(".tar.gz") or suffixes.endswith(".tar.xz"):
        mode = "r:gz" if suffixes.endswith(".tar.gz") else "r"
        with tarfile.open(archive_path, mode) as archive:
            members = [member for member in archive.getmembers() if member.isfile()]
            for member in members:
                if Path(member.name).name == binary_name:
                    handle = archive.extractfile(member)
                    if handle is None:
                        continue
                    extracted = archive_path.parent / binary_name
                    extracted.write_bytes(handle.read())
                    return extracted
    if archive_path.suffix == ".zip":
        with zipfile.ZipFile(archive_path) as archive:
            for name in archive.namelist():
                if Path(name).name == binary_name:
                    extracted = archive_path.parent / binary_name
                    extracted.write_bytes(archive.read(name))
                    return extracted
    if archive_path.name == binary_name or archive_path.name.startswith(binary_name):
        return archive_path
    raise InstallError(f"could not find {binary_name} in downloaded archive")


def github_os() -> str:
    system = sys.platform
    if system == "darwin":
        return "darwin"
    if system.startswith("linux"):
        return "linux"
    if system == "win32":
        return "windows"
    raise InstallError(f"unsupported platform for binary install: {system}")


def github_arch() -> str:
    machine = platform.machine().lower()
    if machine in {"x86_64", "amd64"}:
        return "x86_64"
    if machine in {"arm64", "aarch64"}:
        return "arm64"
    raise InstallError(f"unsupported architecture for binary install: {machine}")
