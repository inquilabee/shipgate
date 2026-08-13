"""Installer protocol and shared helpers."""

from __future__ import annotations

import stat
from typing import TYPE_CHECKING, Protocol
from urllib.parse import urljoin, urlparse

import requests

from shipgate.errors import InstallError

if TYPE_CHECKING:
    from pathlib import Path

    from shipgate.domain.catalog import InstallDefinition

GITHUB_HOSTS = frozenset({"github.com", "api.github.com", "githubusercontent.com"})
GITHUB_HOST_SUFFIXES = (".github.com", ".githubusercontent.com")
GITHUB_REDIRECT_MAX_HOPS = 5
GITHUB_REDIRECT_STATUSES = frozenset({301, 302, 303, 307, 308})


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


class GitHubUrlFetcher:
    """GET a GitHub URL, walking redirects without fetching an off-site hop."""

    def __init__(self, *, timeout: float, headers: dict[str, str] | None = None) -> None:
        self._timeout = timeout
        self._headers = headers

    def fetch(self, url: str) -> requests.Response:
        self.require_github_https(url, "refusing untrusted download URL")
        current = url
        try:
            for _ in range(GITHUB_REDIRECT_MAX_HOPS):
                self.require_github_https(current, "refusing redirect off github.com")
                response = requests.get(
                    current,
                    timeout=self._timeout,
                    allow_redirects=False,
                    headers=self._headers,
                )
                location = self.redirect_location(response)
                if location is None:
                    response.raise_for_status()
                    self.require_github_https(
                        response.url or current,
                        "refusing redirect off github.com",
                    )
                    return response
                current = urljoin(current, location)
        except requests.RequestException as exc:
            raise InstallError(f"failed to fetch {url}: {exc}") from exc
        raise InstallError(f"too many redirects fetching {url}")

    @staticmethod
    def is_github_netloc(netloc: str) -> bool:
        host = netloc.lower().split(":")[0]
        return host in GITHUB_HOSTS or host.endswith(GITHUB_HOST_SUFFIXES)

    @staticmethod
    def require_github_https(url: str, message: str) -> None:
        parsed = urlparse(url)
        if parsed.scheme != "https" or not GitHubUrlFetcher.is_github_netloc(parsed.netloc):
            raise InstallError(f"{message}: {url}")

    @staticmethod
    def redirect_location(response: requests.Response) -> str | None:
        if response.status_code not in GITHUB_REDIRECT_STATUSES:
            return None
        location = response.headers.get("Location")
        if not location:
            raise InstallError(f"redirect missing Location: {response.url}")
        return location


def get_github_url(
    url: str,
    *,
    timeout: float,
    headers: dict[str, str] | None = None,
) -> requests.Response:
    return GitHubUrlFetcher(timeout=timeout, headers=headers).fetch(url)


def download_https_file(url: str, destination: Path) -> None:
    destination.write_bytes(get_github_url(url, timeout=120).content)
