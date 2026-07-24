"""GitHub release binary installer strategy."""

from __future__ import annotations

import json
import platform
import shutil
import sys
import tarfile
import tempfile
import urllib.request
import zipfile
from pathlib import Path
from typing import TYPE_CHECKING

from shipgate.errors import InstallError
from shipgate.runtime.installers.base import download_https_file
from shipgate.runtime.installers.binary_releases import BINARY_RELEASES

if TYPE_CHECKING:
    from shipgate.domain.catalog import InstallDefinition


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
        version = self.normalize_version(install_def.version or "latest")
        url, asset_name = self.build_github_release_url(binary_name, version)
        with tempfile.TemporaryDirectory() as tmp:
            archive_path = Path(tmp) / asset_name
            try:
                download_https_file(url, archive_path)
            except OSError as exc:
                raise InstallError(f"failed to download {binary_name}: {exc}") from exc
            extracted = self.extract_binary(
                archive_path,
                BINARY_RELEASES[binary_name].binary_name,
            )
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(extracted, destination)
            destination.chmod(destination.stat().st_mode | 0o100)

    @staticmethod
    def release_arch(binary_name: str, arch: str) -> str:
        release = BINARY_RELEASES[binary_name]
        return release.arch_map.get(arch, arch)

    @staticmethod
    def github_os() -> str:
        system = sys.platform
        if system == "darwin":
            return "darwin"
        if system.startswith("linux"):
            return "linux"
        if system == "win32":
            return "windows"
        raise InstallError(f"unsupported platform for binary install: {system}")

    @staticmethod
    def github_arch() -> str:
        machine = platform.machine().lower()
        if machine in {"x86_64", "amd64"}:
            return "x86_64"
        if machine in {"arm64", "aarch64"}:
            return "arm64"
        raise InstallError(f"unsupported architecture for binary install: {machine}")

    @staticmethod
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

    @staticmethod
    def resolve_release_version(repo: str, version: str) -> str:
        if version != "latest":
            return version
        return GitHubReleaseInstaller.fetch_latest_release_tag(repo)

    @staticmethod
    def build_github_release_url(binary_name: str, version: str) -> tuple[str, str]:
        release = BINARY_RELEASES[binary_name]
        repo = release.repo
        resolved_version = GitHubReleaseInstaller.resolve_release_version(repo, version)
        asset_name = release.asset_template.format(
            version=resolved_version.lstrip("v"),
            os=GitHubReleaseInstaller.github_os(),
            arch=GitHubReleaseInstaller.release_arch(
                binary_name, GitHubReleaseInstaller.github_arch()
            ),
        )
        if version == "latest":
            url = f"https://github.com/{repo}/releases/latest/download/{asset_name}"
        else:
            url = f"https://github.com/{repo}/releases/download/{resolved_version}/{asset_name}"
        return url, asset_name

    @staticmethod
    def normalize_version(version: str) -> str:
        cleaned = version.strip()
        if cleaned.startswith(">="):
            return "latest"
        return cleaned

    @staticmethod
    def missing_archive_binary(binary_name: str) -> InstallError:
        return InstallError(f"could not find {binary_name} in downloaded archive")

    @staticmethod
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
        raise GitHubReleaseInstaller.missing_archive_binary(binary_name)

    @staticmethod
    def extract_from_zip(archive_path: Path, binary_name: str) -> Path:
        with zipfile.ZipFile(archive_path) as archive:
            for name in archive.namelist():
                if Path(name).name != binary_name:
                    continue
                extracted = archive_path.parent / binary_name
                extracted.write_bytes(archive.read(name))
                return extracted
        raise GitHubReleaseInstaller.missing_archive_binary(binary_name)

    @staticmethod
    def extract_binary(archive_path: Path, binary_name: str) -> Path:
        suffixes = "".join(archive_path.suffixes)
        if suffixes.endswith(".tar.gz") or suffixes.endswith(".tar.xz"):
            return GitHubReleaseInstaller.extract_from_tar(
                archive_path, binary_name, gz=suffixes.endswith(".tar.gz")
            )
        if archive_path.suffix == ".zip":
            return GitHubReleaseInstaller.extract_from_zip(archive_path, binary_name)
        if archive_path.name == binary_name or archive_path.name.startswith(binary_name):
            return archive_path
        raise GitHubReleaseInstaller.missing_archive_binary(binary_name)
