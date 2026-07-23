"""Binary tool installers."""

from __future__ import annotations

import json
import os
import platform
import shutil
import sys
import tarfile
import tempfile
import urllib.request
import zipfile
from pathlib import Path
from typing import TYPE_CHECKING, Protocol

from shipgate.core.process import run_command
from shipgate.errors import InstallError
from shipgate.paths import PROJECT_MANAGED_BIN_DIR
from shipgate.runtime.installers.base import download_https_file, link_binary

if TYPE_CHECKING:
    from shipgate.domain.catalog import InstallDefinition

BINARY_RELEASES: dict[str, dict[str, str | dict[str, str]]] = {
    "gitleaks": {
        "repo": "gitleaks/gitleaks",
        "asset_template": "gitleaks_{version}_{os}_{arch}.tar.gz",
        "binary_name": "gitleaks",
        "arch_map": {"x86_64": "x64"},
    },
    "shfmt": {
        "repo": "mvdan/sh",
        "asset_template": "shfmt_v{version}_{os}_{arch}",
        "binary_name": "shfmt",
        "arch_map": {"x86_64": "amd64"},
    },
    "yamlfmt": {
        "repo": "google/yamlfmt",
        "asset_template": "yamlfmt_{version}_Linux_{arch}.tar.gz",
        "binary_name": "yamlfmt",
        "arch_map": {"x86_64": "x86_64", "arm64": "arm64"},
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
        if binary_name == "yamlfmt":
            return False
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
        version = normalize_version(install_def.version or "latest")
        url, asset_name = build_github_release_url(binary_name, version)
        with tempfile.TemporaryDirectory() as tmp:
            archive_path = Path(tmp) / asset_name
            try:
                download_https_file(url, archive_path)
            except OSError as exc:
                raise InstallError(f"failed to download {binary_name}: {exc}") from exc
            extracted = extract_binary(
                archive_path,
                str(BINARY_RELEASES[binary_name]["binary_name"]),
            )
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(extracted, destination)
            destination.chmod(destination.stat().st_mode | 0o100)


class NpmInstaller:
    def can_install(self, binary_name: str, install_def: InstallDefinition) -> bool:
        return (
            install_def.manager == "binary"
            and binary_name not in BINARY_RELEASES
            and binary_name != "yamlfmt"
        )

    def install(
        self,
        bin_dir: Path,
        binary_name: str,
        install_def: InstallDefinition,
        destination: Path,
    ) -> None:
        npm = shutil.which("npm")
        if npm is None:
            raise InstallError(f"npm is required to install {install_def.package}")
        result = run_command(
            [npm, "install", "--prefix", str(bin_dir), install_def.package],
        )
        if result.returncode != 0:
            raise InstallError(
                f"failed to install {install_def.package}: {result.stderr.strip()}",
            )
        installed = bin_dir / "node_modules" / ".bin" / binary_name
        if sys.platform == "win32":
            installed = installed.with_suffix(".cmd")
        if not installed.is_file():
            raise InstallError(f"{install_def.package} install did not produce an executable")
        link_binary(installed, destination)


class GoInstaller:
    def can_install(self, binary_name: str, install_def: InstallDefinition) -> bool:
        return binary_name == "yamlfmt" and binary_name not in BINARY_RELEASES

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
        result = run_command(
            [go, "install", "github.com/google/yamlfmt/cmd/yamlfmt@latest"],
            env={**os.environ, "GOBIN": str(bin_dir)},
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
        bin_dir = project_root / PROJECT_MANAGED_BIN_DIR
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


def release_arch(binary_name: str, arch: str) -> str:
    release = BINARY_RELEASES[binary_name]
    arch_map = release.get("arch_map")
    if isinstance(arch_map, dict):
        return arch_map.get(arch, arch)
    return arch


def build_github_release_url(binary_name: str, version: str) -> tuple[str, str]:
    release = BINARY_RELEASES[binary_name]
    repo = str(release["repo"])
    resolved_version = resolve_release_version(repo, version)
    asset_name = str(release["asset_template"]).format(
        version=resolved_version.lstrip("v"),
        os=github_os(),
        arch=release_arch(binary_name, github_arch()),
    )
    if version == "latest":
        url = f"https://github.com/{repo}/releases/latest/download/{asset_name}"
    else:
        url = f"https://github.com/{repo}/releases/download/{resolved_version}/{asset_name}"
    return url, asset_name


def resolve_release_version(repo: str, version: str) -> str:
    if version != "latest":
        return version
    return fetch_latest_release_tag(repo)


def fetch_latest_release_tag(repo: str) -> str:
    url = f"https://api.github.com/repos/{repo}/releases/latest"
    request = urllib.request.Request(  # noqa: S310
        url,
        method="GET",
        headers={"Accept": "application/vnd.github+json"},
    )
    try:
        # nosemgrep: python.lang.security.audit.dynamic-urllib-use-detected.dynamic-urllib-use-detected  # noqa: E501
        with urllib.request.urlopen(request, timeout=30) as response:  # noqa: S310  # nosec B310
            data = json.loads(response.read())
    except OSError as exc:
        raise InstallError(f"failed to resolve latest release for {repo}: {exc}") from exc
    tag_name = data.get("tag_name") if isinstance(data, dict) else None
    if not isinstance(tag_name, str) or not tag_name:
        raise InstallError(f"could not resolve latest release for {repo}")
    return tag_name


def normalize_version(version: str) -> str:
    cleaned = version.strip()
    if cleaned.startswith(">="):
        return "latest"
    return cleaned


def extract_binary(archive_path: Path, binary_name: str) -> Path:
    suffixes = "".join(archive_path.suffixes)
    if suffixes.endswith(".tar.gz") or suffixes.endswith(".tar.xz"):
        return extract_from_tar(archive_path, binary_name, gz=suffixes.endswith(".tar.gz"))
    if archive_path.suffix == ".zip":
        return extract_from_zip(archive_path, binary_name)
    if archive_path.name == binary_name or archive_path.name.startswith(binary_name):
        return archive_path
    raise InstallError(f"could not find {binary_name} in downloaded archive")


def extract_from_tar(archive_path: Path, binary_name: str, *, gz: bool) -> Path:
    mode = "r:gz" if gz else "r"
    with tarfile.open(archive_path, mode) as archive:
        for member in archive.getmembers():
            if not member.isfile() or Path(member.name).name != binary_name:
                continue
            handle = archive.extractfile(member)
            if handle is None:
                continue
            extracted = archive_path.parent / binary_name
            extracted.write_bytes(handle.read())
            return extracted
    raise InstallError(f"could not find {binary_name} in downloaded archive")


def extract_from_zip(archive_path: Path, binary_name: str) -> Path:
    with zipfile.ZipFile(archive_path) as archive:
        for name in archive.namelist():
            if Path(name).name != binary_name:
                continue
            extracted = archive_path.parent / binary_name
            extracted.write_bytes(archive.read(name))
            return extracted
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
