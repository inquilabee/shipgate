"""Helpers for turning catalog version pins into installer specs."""

from __future__ import annotations

from shipgate.errors import InstallError


def clean_pin(version: str) -> str:
    stripped = version.strip()
    return stripped[2:].strip() if stripped.startswith("==") else stripped


def assert_exact_pin(version: str, *, kind: str) -> str:
    cleaned = clean_pin(version)
    if not cleaned:
        raise InstallError(f"{kind} install requires an exact version pin")
    if cleaned.startswith((">=", "<=", ">", "<", "~=", "!=")) or cleaned == "*":
        raise InstallError(f"{kind} install requires an exact version pin, got {version!r}")
    return cleaned


def pip_package_spec(package: str, version: str) -> str:
    if not version.strip():
        return package
    cleaned = version.strip()
    return (
        f"{package}{cleaned}"
        if cleaned.startswith(("=", "<", ">", "~", "!"))
        else f"{package}=={clean_pin(cleaned)}"
    )


def npm_package_spec(package: str, version: str) -> str:
    if not version.strip():
        return package
    cleaned = assert_exact_pin(version, kind="npm")
    return f"{package}@{cleaned}"
