"""GitHub release binary installer strategy."""

from __future__ import annotations

import platform
import shutil
import sys
import tarfile
import tempfile
import zipfile
from pathlib import Path
from typing import TYPE_CHECKING

from shipgate.errors import InstallError
from shipgate.paths import contained_child
from shipgate.runtime.installers.base import download_https_file, get_github_url

if TYPE_CHECKING:
    from shipgate.domain.catalog import BinaryDownloadSpec, InstallDefinition


class GitHubReleaseInstaller:
    @staticmethod
    def can_install(binary_name: str, install_def: InstallDefinition) -> bool:
        _ = binary_name
        return install_def.download is not None

    def install(
        self,
        bin_dir: Path,
        binary_name: str,
        install_def: InstallDefinition,
        destination: Path,
    ) -> None:
        _ = bin_dir
        download = install_def.download
        if download is None:
            raise InstallError(f"binary {binary_name!r} has no install.download metadata")
        version = self.normalize_version(install_def.version)
        url, asset_name = self.build_github_release_url(download, version)
        with tempfile.TemporaryDirectory() as tmp:
            try:
                archive_path = contained_child(Path(tmp), asset_name)
            except ValueError as exc:
                raise InstallError(f"asset name escapes download dir: {asset_name!r}") from exc
            try:
                download_https_file(url, archive_path)
            except OSError as exc:
                raise InstallError(f"failed to download {binary_name}: {exc}") from exc
            extracted = self.extract_binary(archive_path, download.binary_name)
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(extracted, destination)
            destination.chmod(destination.stat().st_mode | 0o100)

    @staticmethod
    def release_arch(download: BinaryDownloadSpec, arch: str) -> str:
        return download.arch_map.get(arch, arch)

    def release_os(self, download: BinaryDownloadSpec) -> str:
        system = self.github_os()
        return download.os_map.get(system, system)

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
        try:
            data = get_github_url(
                url,
                timeout=30,
                headers={"Accept": "application/vnd.github+json"},
            ).json()
        except (InstallError, ValueError) as exc:
            raise InstallError(f"failed to resolve latest release for {repo}: {exc}") from exc
        tag_name = data.get("tag_name") if isinstance(data, dict) else None
        if not isinstance(tag_name, str) or not tag_name:
            raise InstallError(f"could not resolve latest release for {repo}")
        return tag_name

    def resolve_release_version(self, repo: str, version: str) -> str:
        return (
            version
            if version.startswith("v")
            else (
                f"v{version.lstrip('v')}"
                if version != "latest"
                else self.fetch_latest_release_tag(repo)
            )
        )

    def build_github_release_url(
        self,
        download: BinaryDownloadSpec,
        version: str,
    ) -> tuple[str, str]:
        repo = download.repo
        resolved_version = self.resolve_release_version(repo, version)
        asset_name = download.asset_template.format(
            version=resolved_version.lstrip("v"),
            os=self.release_os(download),
            arch=self.release_arch(download, self.github_arch()),
        )
        url = (
            f"https://github.com/{repo}/releases/latest/download/{asset_name}"
            if version == "latest"
            else f"https://github.com/{repo}/releases/download/{resolved_version}/{asset_name}"
        )
        return url, asset_name

    @staticmethod
    def normalize_version(version: str) -> str:
        cleaned = version.strip()
        if not cleaned:
            raise InstallError("binary install requires an exact version pin")
        if cleaned.startswith((">=", "<=", ">", "<", "~=", "!=")) or cleaned == "*":
            raise InstallError(f"binary install requires an exact version pin, got {cleaned!r}")
        if cleaned.startswith("=="):
            cleaned = cleaned[2:].strip()
        return cleaned

    @staticmethod
    def missing_archive_binary(binary_name: str) -> InstallError:
        return InstallError(f"could not find {binary_name} in downloaded archive")

    def extract_from_tar(
        self,
        archive_path: Path,
        binary_name: str,
        *,
        xz: bool = False,
        gz: bool = False,
    ) -> Path:
        mode = "r:xz" if xz else "r:gz" if gz else "r"
        try:
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
        except (OSError, tarfile.TarError) as exc:
            raise InstallError(
                f"failed to extract {binary_name} from {archive_path.name}: {exc}"
            ) from exc
        raise self.missing_archive_binary(binary_name)

    def extract_from_zip(self, archive_path: Path, binary_name: str) -> Path:
        with zipfile.ZipFile(archive_path) as archive:
            for name in archive.namelist():
                if Path(name).name != binary_name:
                    continue
                extracted = archive_path.parent / binary_name
                extracted.write_bytes(archive.read(name))
                return extracted
        raise self.missing_archive_binary(binary_name)

    def extract_binary(self, archive_path: Path, binary_name: str) -> Path:
        suffixes = "".join(archive_path.suffixes)
        if suffixes.endswith(".tar.xz"):
            return self.extract_from_tar(archive_path, binary_name, xz=True)
        if suffixes.endswith(".tar.gz"):
            return self.extract_from_tar(archive_path, binary_name, gz=True)
        if archive_path.suffix == ".zip":
            return self.extract_from_zip(archive_path, binary_name)
        if archive_path.name == binary_name or archive_path.name.startswith(binary_name):
            return archive_path
        raise self.missing_archive_binary(binary_name)
