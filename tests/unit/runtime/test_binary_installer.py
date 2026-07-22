from unittest.mock import patch

import pytest

from shipgate.catalog.loader import load_catalog
from shipgate.domain.catalog import InstallDefinition
from shipgate.runtime.installers.binary import (
    NpmInstaller,
    build_github_release_url,
    release_arch,
)


@pytest.mark.parametrize(
    ("binary_name", "arch", "expected"),
    [
        ("gitleaks", "x86_64", "x64"),
        ("gitleaks", "arm64", "arm64"),
        ("shfmt", "x86_64", "amd64"),
        ("shfmt", "arm64", "arm64"),
        ("shellcheck", "x86_64", "x86_64"),
    ],
)
def test_release_arch_mapping(binary_name, arch, expected):
    assert release_arch(binary_name, arch) == expected


@patch("shipgate.runtime.installers.binary.github_os", return_value="linux")
@patch("shipgate.runtime.installers.binary.github_arch", return_value="x86_64")
def test_gitleaks_release_url_uses_x64_arch(_mock_arch, _mock_os):
    url, asset_name = build_github_release_url("gitleaks", "v8.18.2")
    assert asset_name == "gitleaks_8.18.2_linux_x64.tar.gz"
    assert url.endswith("/releases/download/v8.18.2/gitleaks_8.18.2_linux_x64.tar.gz")


@patch("shipgate.runtime.installers.binary.github_os", return_value="linux")
@patch("shipgate.runtime.installers.binary.github_arch", return_value="x86_64")
def test_shfmt_release_url_uses_amd64_arch(_mock_arch, _mock_os):
    url, asset_name = build_github_release_url("shfmt", "v3.8.0")
    assert asset_name == "shfmt_v3.8.0_linux_amd64"
    assert url.endswith("/releases/download/v3.8.0/shfmt_v3.8.0_linux_amd64")


@patch("shipgate.runtime.installers.binary.fetch_latest_release_tag", return_value="v8.30.1")
@patch("shipgate.runtime.installers.binary.github_os", return_value="linux")
@patch("shipgate.runtime.installers.binary.github_arch", return_value="x86_64")
def test_gitleaks_latest_release_url_resolves_tag(_mock_arch, _mock_os, _mock_latest):
    url, asset_name = build_github_release_url("gitleaks", "latest")
    assert asset_name == "gitleaks_8.30.1_linux_x64.tar.gz"
    assert "/releases/latest/download/" in url


@patch("shipgate.runtime.installers.binary.fetch_latest_release_tag", return_value="v3.13.1")
@patch("shipgate.runtime.installers.binary.github_os", return_value="linux")
@patch("shipgate.runtime.installers.binary.github_arch", return_value="x86_64")
def test_shfmt_latest_release_url_resolves_tag(_mock_arch, _mock_os, _mock_latest):
    _url, asset_name = build_github_release_url("shfmt", "latest")
    assert asset_name == "shfmt_v3.13.1_linux_amd64"


@patch("shipgate.runtime.installers.binary.github_os", return_value="linux")
@patch("shipgate.runtime.installers.binary.github_arch", return_value="x86_64")
def test_shellcheck_release_url_keeps_x86_64_arch(_mock_arch, _mock_os):
    _url, asset_name = build_github_release_url("shellcheck", "v0.10.0")
    assert asset_name == "shellcheck-0.10.0-linux.x86_64.tar.xz"


def test_npm_installer_handles_jscpd():
    catalog = load_catalog()
    install_def = catalog.get_tool("jscpd.check.python").install
    assert install_def is not None
    installer = NpmInstaller()
    assert installer.can_install("jscpd", install_def)


def test_npm_installer_handles_markdownlint():
    catalog = load_catalog()
    install_def = catalog.get_tool("markdownlint.check").install
    assert install_def is not None
    installer = NpmInstaller()
    assert installer.can_install("markdownlint", install_def)


def test_npm_installer_skips_github_binaries():
    install_def = InstallDefinition(manager="binary", package="gitleaks", binary="gitleaks")
    installer = NpmInstaller()
    assert not installer.can_install("gitleaks", install_def)


def test_npm_installer_skips_yamlfmt_for_go_installer():
    install_def = InstallDefinition(manager="binary", package="yamlfmt", binary="yamlfmt")
    installer = NpmInstaller()
    assert not installer.can_install("yamlfmt", install_def)
