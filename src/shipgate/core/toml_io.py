"""Shared TOML loading helpers."""

from __future__ import annotations

import tomllib
from typing import TYPE_CHECKING

from shipgate.errors import ConfigError

if TYPE_CHECKING:
    from pathlib import Path


def load_toml_mapping(
    path: Path,
    *,
    error_cls: type[Exception] = ConfigError,
    invalid_message: str | None = None,
) -> dict:
    try:
        raw = tomllib.loads(path.read_text(encoding="utf-8"))
    except tomllib.TOMLDecodeError as exc:
        message = invalid_message or f"invalid TOML: {exc}"
        raise_toml_mapping_error(error_cls, message, path, cause=exc)
    if not isinstance(raw, dict):
        message = invalid_message or "TOML document must be a mapping"
        raise_toml_mapping_error(error_cls, message, path)
    return raw


def raise_toml_mapping_error(
    error_cls: type[Exception],
    message: str,
    path: Path,
    *,
    cause: Exception | None = None,
) -> None:
    if issubclass(error_cls, ConfigError):
        raise error_cls(message, path=str(path)) from cause
    raise error_cls(message) from cause
