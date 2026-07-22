"""Shared YAML loading helpers."""

from __future__ import annotations

from typing import TYPE_CHECKING

import yaml

from shipgate.errors import CatalogError, ConfigError

if TYPE_CHECKING:
    from pathlib import Path


def load_yaml_mapping(
    path: Path,
    *,
    error_cls: type[Exception] = ConfigError,
    invalid_message: str | None = None,
) -> dict:
    try:
        raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        message = invalid_message or f"invalid YAML: {exc}"
        raise_yaml_mapping_error(error_cls, message, path, cause=exc)
    if raw is None:
        return {}
    if not isinstance(raw, dict):
        message = invalid_message or "YAML document must be a mapping"
        raise_yaml_mapping_error(error_cls, message, path)
    return dict(raw)


def raise_yaml_mapping_error(
    error_cls: type[Exception],
    message: str,
    path: Path,
    *,
    cause: Exception | None = None,
) -> None:
    if issubclass(error_cls, (ConfigError, CatalogError)):
        raise error_cls(message, path=str(path)) from cause
    raise error_cls(message) from cause
