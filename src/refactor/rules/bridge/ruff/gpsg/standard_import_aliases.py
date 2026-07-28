"""Shared ICN001 bridges for GPSG standard import aliases."""

from __future__ import annotations

from typing import ClassVar

from refactor.protocol import Hit, RuleKind
from refactor.rules.bridge.ruff.ruff_bridge import RuffBridge

ICN_EXTEND_ALIASES = (
    "lint.flake8-import-conventions.extend-aliases="
    '{datetime="dt",tkinter="tk",multiprocessing="mp"}'
)

ALIAS_SPECS: tuple[tuple[str, str, str], ...] = (
    ("use-standard-name-for-aliases-pandas", "pandas", "pd"),
    ("use-standard-name-for-aliases-numpy", "numpy", "np"),
    ("use-standard-name-for-aliases-matplotlib-pyplot", "matplotlib.pyplot", "plt"),
    ("use-standard-name-for-aliases-tensorflow", "tensorflow", "tf"),
    ("use-standard-name-for-aliases-datetime", "datetime", "dt"),
    ("use-standard-name-for-aliases-tkinter", "tkinter", "tk"),
    ("use-standard-name-for-aliases-multiprocessing", "multiprocessing", "mp"),
)


class GpsgStandardImportAliasBridge(RuffBridge):
    """One ICN001 select; subclasses filter diagnostics to a module/alias pair."""

    kind = RuleKind.SUGGESTION
    delegates_to = "ICN001"
    ruff_config = (ICN_EXTEND_ALIASES,)
    module_name: ClassVar[str]
    expected_alias: ClassVar[str]

    def detect(self, source: str, path: str) -> list[Hit]:
        return [
            hit
            for hit in super().detect(source, path)
            if self.matches_module(str(hit.extra.get("ruff_message") or ""))
        ]

    def matches_module(self, ruff_message: str) -> bool:
        needle = f"`{self.module_name}` should be imported as `{self.expected_alias}`"
        return needle in ruff_message


def build_alias_bridge(rule_id: str, module_name: str, expected_alias: str) -> type:
    return type(
        f"GpsgAlias_{module_name.replace('.', '_')}",
        (GpsgStandardImportAliasBridge,),
        {
            "rule_id": rule_id,
            "summary": f"Import `{module_name}` as `{expected_alias}`",
            "message": f"Import `{module_name}` as `{expected_alias}`",
            "module_name": module_name,
            "expected_alias": expected_alias,
        },
    )


GPSG_IMPORT_ALIAS_BRIDGES = tuple(
    build_alias_bridge(rule_id, module, alias)() for rule_id, module, alias in ALIAS_SPECS
)
