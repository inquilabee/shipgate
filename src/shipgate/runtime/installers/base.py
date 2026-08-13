"""Installer protocol and shared helpers."""

from __future__ import annotations

import stat
from typing import TYPE_CHECKING, Protocol
from urllib.parse import urlparse

import requests

from shipgate.errors import InstallError

if TYPE_CHECKING:
    from pathlib import Path

    from shipgate.domain.catalog import InstallDefinition

GITHUB_HOSTS = frozenset({"github.com", "api.github.com", "githubusercontent.com"})
GITHUB_HOST_SUFFIXES = (".github.com", ".githubusercontent.com")


class Installer(Protocol):
    manager: str

    def install_packages(
        self,
        project_root: Path,
        packages: dict[str, InstallDefinition],
        *,
        force: bool = False,
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


def is_github_netloc(netloc: str) -> bool:
    host = netloc.lower().split(":")[0]
    return host in GITHUB_HOSTS or host.endswith(GITHUB_HOST_SUFFIXES)


def get_github_url(
    url: str,
    *,
    timeout: float,
    headers: dict[str, str] | None = None,
) -> requests.Response:
    parsed = urlparse(url)
    if parsed.scheme != "https" or not is_github_netloc(parsed.netloc):
        raise InstallError(f"refusing untrusted download URL: {url}")
    try:
        response = requests.get(url, timeout=timeout, allow_redirects=True, headers=headers)
        response.raise_for_status()
    except requests.RequestException as exc:
        raise InstallError(f"failed to fetch {url}: {exc}") from exc
    final = urlparse(response.url)
    if final.scheme != "https" or not is_github_netloc(final.netloc):
        raise InstallError(f"refusing redirect off github.com: {response.url}")
    return response


def download_https_file(url: str, destination: Path) -> None:
    destination.write_bytes(get_github_url(url, timeout=120).content)
