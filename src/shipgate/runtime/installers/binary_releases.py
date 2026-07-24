"""Typed GitHub release metadata for managed binary installs."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class ReleaseSpec:
    repo: str
    asset_template: str
    binary_name: str
    arch_map: dict[str, str] = field(default_factory=dict)


BINARY_RELEASES: dict[str, ReleaseSpec] = {
    "gitleaks": ReleaseSpec(
        repo="gitleaks/gitleaks",
        asset_template="gitleaks_{version}_{os}_{arch}.tar.gz",
        binary_name="gitleaks",
        arch_map={"x86_64": "x64"},
    ),
    "shfmt": ReleaseSpec(
        repo="mvdan/sh",
        asset_template="shfmt_v{version}_{os}_{arch}",
        binary_name="shfmt",
        arch_map={"x86_64": "amd64"},
    ),
    "yamlfmt": ReleaseSpec(
        repo="google/yamlfmt",
        asset_template="yamlfmt_{version}_Linux_{arch}.tar.gz",
        binary_name="yamlfmt",
        arch_map={"x86_64": "x86_64", "arm64": "arm64"},
    ),
    "shellcheck": ReleaseSpec(
        repo="koalaman/shellcheck",
        asset_template="shellcheck-{version}-{os}.{arch}.tar.xz",
        binary_name="shellcheck",
    ),
}
