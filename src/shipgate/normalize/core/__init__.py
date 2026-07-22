"""Normalize framework: protocols, base classes, and shared helpers."""

from shipgate.normalize.core.base import BaseNormalizer, Normalizer
from shipgate.normalize.core.exit import (
    CodespellNormalizer,
    DeadcodeNormalizer,
    MarkdownlintNormalizer,
    VultureNormalizer,
)
from shipgate.normalize.core.gate_json import GateJsonNormalizer
from shipgate.normalize.core.generic import GenericExitNormalizer
from shipgate.normalize.core.json import JsonItemsNormalizer, JsonNormalizer
from shipgate.normalize.core.utils import (
    decode_json_payload,
    empty_pass_report,
    extract_items,
    findings_report,
    read_tool_output,
    tool_exit_report,
)

__all__ = [
    "BaseNormalizer",
    "CodespellNormalizer",
    "DeadcodeNormalizer",
    "GateJsonNormalizer",
    "GenericExitNormalizer",
    "JsonItemsNormalizer",
    "JsonNormalizer",
    "MarkdownlintNormalizer",
    "Normalizer",
    "VultureNormalizer",
    "decode_json_payload",
    "empty_pass_report",
    "extract_items",
    "findings_report",
    "read_tool_output",
    "tool_exit_report",
]
