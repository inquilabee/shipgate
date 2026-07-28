"""GPSG Ruff bridge rules (optional ``gpsg`` pack)."""

from __future__ import annotations

from refactor.rules.bridge.ruff.gpsg.errors_named_error import ErrorsNamedErrorBridge
from refactor.rules.bridge.ruff.gpsg.map_lambda_to_generator import (
    MapLambdaToGeneratorBridge,
)
from refactor.rules.bridge.ruff.gpsg.no_long_functions import NoLongFunctionsBridge
from refactor.rules.bridge.ruff.gpsg.no_relative_imports import NoRelativeImportsBridge
from refactor.rules.bridge.ruff.gpsg.no_wildcard_imports import NoWildcardImportsBridge
from refactor.rules.bridge.ruff.gpsg.standard_import_aliases import (
    GPSG_IMPORT_ALIAS_BRIDGES,
)

RULES = (
    NoWildcardImportsBridge(),
    NoRelativeImportsBridge(),
    *GPSG_IMPORT_ALIAS_BRIDGES,
    ErrorsNamedErrorBridge(),
    MapLambdaToGeneratorBridge(),
    NoLongFunctionsBridge(),
)

__all__ = ["RULES"]
