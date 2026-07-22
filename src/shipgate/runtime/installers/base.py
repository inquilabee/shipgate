"""Installer protocol and shared helpers."""

from __future__ import annotations

import stat
import urllib.parse
import urllib.request
from typing import TYPE_CHECKING, Protocol

from shipgate.errors import InstallError

if TYPE_CHECKING:
    from pathlib import Path

    from shipgate.domain.catalog import InstallDefinition


class Installer(Protocol):
    manager: str

    def install_packages(
        self,
        project_root: Path,
        packages: dict[str, InstallDefinition],
    ) -> None: ...


def link_binary(source: Path, destination: Path) -> None:
    import shutil

    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists() or destination.is_symlink():
        destination.unlink()
    try:
        destination.symlink_to(source)
    except OSError:
        shutil.copy2(source, destination)
        destination.chmod(destination.stat().st_mode | stat.S_IXUSR)


def download_https_file(url: str, destination: Path) -> None:
    parsed = urllib.parse.urlparse(url)
    if parsed.scheme != "https" or parsed.netloc != "github.com":
        raise InstallError(f"refusing untrusted download URL: {url}")
    request = urllib.request.Request(url, method="GET")  # noqa: S310
    # nosemgrep: python.lang.security.audit.dynamic-urllib-use-detected.dynamic-urllib-use-detected
    with urllib.request.urlopen(request, timeout=120) as response:  # noqa: S310  # nosec B310
        destination.write_bytes(response.read())
