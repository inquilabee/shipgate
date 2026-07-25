from unittest.mock import patch

import pytest

from shipgate.catalog.loader import CatalogLoader
from shipgate.domain.catalog import BinaryDownloadSpec, InstallDefinition
from shipgate.runtime.installers.binary import (
    GitHubReleaseInstaller,
    NpmInstaller,
)


def tool_download(tool_id: str) -> BinaryDownloadSpec:
    catalog = CatalogLoader.load()
    install = catalog.get_tool(tool_id).install
    assert install is not None
    assert install.download is not None
    return install.download


@pytest.mark.parametrize(
    ("tool_id", "arch", "expected"),
    [
        ("gitleaks.scan", "x86_64", "x64"),
        ("gitleaks.scan", "arm64", "arm64"),
        ("shfmt.apply", "x86_64", "amd64"),
        ("shfmt.apply", "arm64", "arm64"),
        ("shellcheck.check", "x86_64", "x86_64"),
    ],
)
def test_release_arch_mapping(tool_id, arch, expected):
    assert GitHubReleaseInstaller.release_arch(tool_download(tool_id), arch) == expected


@patch(
    "shipgate.runtime.installers.binary_github.GitHubReleaseInstaller.github_os",
    return_value="linux",
)
@patch(
    "shipgate.runtime.installers.binary_github.GitHubReleaseInstaller.github_arch",
    return_value="x86_64",
)
def test_gitleaks_release_url_uses_x64_arch(mock_github_arch, mock_github_os):
    assert mock_github_arch.return_value == "x86_64"
    assert mock_github_os.return_value == "linux"
    url, asset_name = GitHubReleaseInstaller.build_github_release_url(
        tool_download("gitleaks.scan"),
        "v8.18.2",
    )
    assert asset_name == "gitleaks_8.18.2_linux_x64.tar.gz"
    assert url.endswith("/releases/download/v8.18.2/gitleaks_8.18.2_linux_x64.tar.gz")


@patch(
    "shipgate.runtime.installers.binary_github.GitHubReleaseInstaller.github_os",
    return_value="linux",
)
@patch(
    "shipgate.runtime.installers.binary_github.GitHubReleaseInstaller.github_arch",
    return_value="x86_64",
)
def test_shfmt_release_url_uses_amd64_arch(mock_github_arch, mock_github_os):
    assert mock_github_arch.return_value == "x86_64"
    assert mock_github_os.return_value == "linux"
    url, asset_name = GitHubReleaseInstaller.build_github_release_url(
        tool_download("shfmt.apply"),
        "v3.8.0",
    )
    assert asset_name == "shfmt_v3.8.0_linux_amd64"
    assert url.endswith("/releases/download/v3.8.0/shfmt_v3.8.0_linux_amd64")


@patch(
    "shipgate.runtime.installers.binary_github.GitHubReleaseInstaller.fetch_latest_release_tag",
    return_value="v8.30.1",
)
@patch(
    "shipgate.runtime.installers.binary_github.GitHubReleaseInstaller.github_os",
    return_value="linux",
)
@patch(
    "shipgate.runtime.installers.binary_github.GitHubReleaseInstaller.github_arch",
    return_value="x86_64",
)
def test_gitleaks_latest_release_url_resolves_tag(
    mock_github_arch,
    mock_github_os,
    mock_fetch_latest,
):
    assert mock_github_arch.return_value == "x86_64"
    assert mock_github_os.return_value == "linux"
    assert mock_fetch_latest.return_value == "v8.30.1"
    url, asset_name = GitHubReleaseInstaller.build_github_release_url(
        tool_download("gitleaks.scan"),
        "latest",
    )
    assert asset_name == "gitleaks_8.30.1_linux_x64.tar.gz"
    assert "/releases/latest/download/" in url


@patch(
    "shipgate.runtime.installers.binary_github.GitHubReleaseInstaller.fetch_latest_release_tag",
    return_value="v3.13.1",
)
@patch(
    "shipgate.runtime.installers.binary_github.GitHubReleaseInstaller.github_os",
    return_value="linux",
)
@patch(
    "shipgate.runtime.installers.binary_github.GitHubReleaseInstaller.github_arch",
    return_value="x86_64",
)
def test_shfmt_latest_release_url_resolves_tag(
    mock_github_arch,
    mock_github_os,
    mock_fetch_latest,
):
    assert mock_github_arch.return_value == "x86_64"
    assert mock_github_os.return_value == "linux"
    assert mock_fetch_latest.return_value == "v3.13.1"
    _url, asset_name = GitHubReleaseInstaller.build_github_release_url(
        tool_download("shfmt.apply"),
        "latest",
    )
    assert asset_name == "shfmt_v3.13.1_linux_amd64"


@patch(
    "shipgate.runtime.installers.binary_github.GitHubReleaseInstaller.github_os",
    return_value="linux",
)
@patch(
    "shipgate.runtime.installers.binary_github.GitHubReleaseInstaller.github_arch",
    return_value="x86_64",
)
def test_shellcheck_release_url_keeps_x86_64_arch(mock_github_arch, mock_github_os):
    assert mock_github_arch.return_value == "x86_64"
    assert mock_github_os.return_value == "linux"
    _url, asset_name = GitHubReleaseInstaller.build_github_release_url(
        tool_download("shellcheck.check"),
        "v0.10.0",
    )
    assert asset_name == "shellcheck-0.10.0-linux.x86_64.tar.xz"


@patch(
    "shipgate.runtime.installers.binary_github.GitHubReleaseInstaller.github_os",
    return_value="linux",
)
@patch(
    "shipgate.runtime.installers.binary_github.GitHubReleaseInstaller.github_arch",
    return_value="x86_64",
)
def test_hadolint_release_url(mock_github_arch, mock_github_os):
    assert mock_github_arch.return_value == "x86_64"
    assert mock_github_os.return_value == "linux"
    url, asset_name = GitHubReleaseInstaller.build_github_release_url(
        tool_download("hadolint.check"),
        "2.14.0",
    )
    assert asset_name == "hadolint-linux-x86_64"
    assert url.endswith("/releases/download/v2.14.0/hadolint-linux-x86_64")


def test_npm_installer_handles_jscpd():
    catalog = CatalogLoader.load()
    install_def = catalog.get_tool("jscpd.check.python").install
    assert install_def is not None
    installer = NpmInstaller()
    assert installer.can_install("jscpd", install_def)


def test_npm_installer_handles_markdownlint():
    catalog = CatalogLoader.load()
    install_def = catalog.get_tool("markdownlint.check").install
    assert install_def is not None
    installer = NpmInstaller()
    assert installer.can_install("markdownlint", install_def)


def test_npm_installer_skips_github_binaries():
    install_def = InstallDefinition(
        manager="binary",
        package="gitleaks",
        binary="gitleaks",
        version="8.30.1",
        download=BinaryDownloadSpec(
            repo="gitleaks/gitleaks",
            asset_template="gitleaks_{version}_{os}_{arch}.tar.gz",
            binary_name="gitleaks",
        ),
    )
    installer = NpmInstaller()
    assert not installer.can_install("gitleaks", install_def)


def test_path_installer_respects_allow_path_false(monkeypatch):
    from shipgate.runtime.installers.binary import PathBinaryInstaller

    monkeypatch.setattr(
        "shipgate.runtime.installers.binary_path.shutil.which",
        lambda _name: "/usr/bin/yamlfmt",
    )
    install_def = InstallDefinition(
        manager="binary",
        package="yamlfmt",
        binary="yamlfmt",
        version="0.21.0",
        allow_path=False,
    )
    installer = PathBinaryInstaller()
    assert not installer.can_install("yamlfmt", install_def)


def test_catalog_yamlfmt_disallows_path():
    catalog = CatalogLoader.load()
    install_def = catalog.get_tool("yamlfmt.apply").install
    assert install_def is not None
    assert install_def.allow_path is False


def test_catalog_pins_are_exact():
    catalog = CatalogLoader.load()
    for tool_id, tool in catalog.tools.items():
        if tool.install is None:
            continue
        version = tool.install.version
        assert version, tool_id
        assert not version.startswith((">=", "<=", "~=")), tool_id
