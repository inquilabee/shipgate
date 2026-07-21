"""Managed tool installation."""

from __future__ import annotations

import json
import os
import platform
import shutil
import stat
import subprocess
import sys
import tarfile
import tempfile
import urllib.parse
import urllib.request
import zipfile
from pathlib import Path
from typing import TYPE_CHECKING

from shipgate.errors import InstallError
from shipgate.paths import managed_bin_dir, managed_python_env, tools_dir
from shipgate.planning.suites import expand_suite
from shipgate.runtime.environment import tools_manifest_path

if TYPE_CHECKING:
    from shipgate.domain.catalog import Catalog, InstallDefinition

MANIFEST_SCHEMA = "shipgate.install.v1"

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


def collect_install_requirements(
    suite_id: str,
    catalog: Catalog,
) -> tuple[dict[str, InstallDefinition], dict[str, InstallDefinition]]:
    tool_ids = expand_suite(suite_id, catalog)
    python_packages: dict[str, InstallDefinition] = {}
    binary_packages: dict[str, InstallDefinition] = {}
    for tool_id in tool_ids:
        tool = catalog.get_tool(tool_id)
        if not tool.install:
            continue
        if tool.install.manager == "python":
            python_packages[tool.install.package] = tool.install
        elif tool.install.manager == "binary":
            key = tool.install.binary or tool.install.package
            binary_packages[key] = tool.install
    return python_packages, binary_packages


def install_suite(project_root: Path, suite_id: str, catalog: Catalog) -> Path:
    python_packages, binary_packages = collect_install_requirements(suite_id, catalog)
    tools_dir(project_root).mkdir(parents=True, exist_ok=True)
    if python_packages:
        _install_python_packages(project_root, python_packages)
    if binary_packages:
        _install_binary_packages(project_root, binary_packages)
    manifest = _read_manifest(project_root)
    manifest.update(
        {
            "schema_version": MANIFEST_SCHEMA,
            "python": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
            "packages": {
                **manifest.get("packages", {}),
                **{
                    pkg: install_def.version or "latest"
                    for pkg, install_def in python_packages.items()
                },
            },
            "binaries": {
                **manifest.get("binaries", {}),
                **{
                    name: install_def.version or "latest"
                    for name, install_def in binary_packages.items()
                },
            },
        }
    )
    manifest_path = tools_manifest_path(project_root)
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return manifest_path


def _read_manifest(project_root: Path) -> dict:
    manifest_path = tools_manifest_path(project_root)
    if not manifest_path.is_file():
        return {}
    data = json.loads(manifest_path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        return {}
    return data


def _install_python_packages(
    project_root: Path,
    packages: dict[str, InstallDefinition],
) -> None:
    venv = managed_python_env(project_root)
    if not venv.exists():
        subprocess.run(  # noqa: S603
            [sys.executable, "-m", "venv", str(venv)],
            check=True,
            capture_output=True,
            text=True,
        )
    if sys.platform == "win32":
        pip = venv / "Scripts" / "pip"
    else:
        pip = venv / "bin" / "pip"
    for package, install_def in sorted(packages.items()):
        spec = package
        if install_def.version:
            spec = f"{package}{install_def.version}"
        result = subprocess.run(  # noqa: S603
            [str(pip), "install", spec],
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode != 0:
            raise InstallError(
                f"failed to install {package}: {result.stderr.strip()}",
            )


def _install_binary_packages(
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
        existing = shutil.which(binary_name)
        if existing:
            _link_binary(Path(existing), destination)
            continue
        if binary_name in BINARY_RELEASES:
            _download_github_binary(binary_name, install_def, destination)
            continue
        if binary_name == "markdownlint":
            _install_markdownlint(bin_dir, destination)
            continue
        if binary_name == "yamlfmt":
            _install_yamlfmt(bin_dir, destination)
            continue
        raise InstallError(
            f"binary {binary_name!r} is not available on PATH and has no managed installer",
            hint="install the tool manually or add it to PATH",
        )


def _link_binary(source: Path, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists() or destination.is_symlink():
        destination.unlink()
    try:
        destination.symlink_to(source)
    except OSError:
        shutil.copy2(source, destination)
        destination.chmod(destination.stat().st_mode | stat.S_IXUSR)


def _install_markdownlint(bin_dir: Path, destination: Path) -> None:
    npm = shutil.which("npm")
    if npm is None:
        raise InstallError("npm is required to install markdownlint-cli")
    prefix = bin_dir
    result = subprocess.run(  # noqa: S603
        [npm, "install", "--prefix", str(prefix), "markdownlint-cli"],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        raise InstallError(f"failed to install markdownlint-cli: {result.stderr.strip()}")
    installed = prefix / "node_modules" / ".bin" / "markdownlint"
    if sys.platform == "win32":
        installed = installed.with_suffix(".cmd")
    if not installed.is_file():
        raise InstallError("markdownlint-cli install did not produce an executable")
    _link_binary(installed, destination)


def _install_yamlfmt(bin_dir: Path, destination: Path) -> None:
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


def _download_github_binary(
    binary_name: str,
    install_def: InstallDefinition,
    destination: Path,
) -> None:
    release = BINARY_RELEASES[binary_name]
    version = _normalize_version(install_def.version or "latest")
    asset_name = release["asset_template"].format(
        version=version.lstrip("v"),
        os=_github_os(),
        arch=_github_arch(),
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
            _download_https_file(url, archive_path)
        except OSError as exc:
            raise InstallError(f"failed to download {binary_name}: {exc}") from exc
        extracted = _extract_binary(archive_path, release["binary_name"])
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(extracted, destination)
        destination.chmod(destination.stat().st_mode | stat.S_IXUSR)


def _extract_binary(archive_path: Path, binary_name: str) -> Path:
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


def _normalize_version(version: str) -> str:
    cleaned = version.strip()
    if cleaned.startswith(">="):
        return "latest"
    return cleaned


def _download_https_file(url: str, destination: Path) -> None:
    parsed = urllib.parse.urlparse(url)
    if parsed.scheme != "https" or parsed.netloc != "github.com":
        raise InstallError(f"refusing untrusted download URL: {url}")
    request = urllib.request.Request(url, method="GET")  # noqa: S310
    # nosemgrep: python.lang.security.audit.dynamic-urllib-use-detected.dynamic-urllib-use-detected
    with urllib.request.urlopen(request, timeout=120) as response:  # noqa: S310  # nosec B310
        destination.write_bytes(response.read())


def _github_os() -> str:
    system = sys.platform
    if system == "darwin":
        return "darwin"
    if system.startswith("linux"):
        return "linux"
    if system == "win32":
        return "windows"
    raise InstallError(f"unsupported platform for binary install: {system}")


def _github_arch() -> str:
    machine = platform.machine().lower()
    if machine in {"x86_64", "amd64"}:
        return "x86_64"
    if machine in {"arm64", "aarch64"}:
        return "arm64"
    raise InstallError(f"unsupported architecture for binary install: {machine}")
