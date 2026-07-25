"""Normalize framework: protocols, base classes, and shared helpers."""

from .base import BaseNormalizer, Normalizer  # ruff:ignore[unused-import]
from .exit import (  # ruff:ignore[unused-import]
    CodespellNormalizer,
    DeadcodeNormalizer,
    MarkdownlintNormalizer,
    VultureNormalizer,
)
from .gate_json import GateJsonNormalizer  # ruff:ignore[unused-import]
from .generic import GenericExitNormalizer  # ruff:ignore[unused-import]
from .json import JsonItemsNormalizer  # ruff:ignore[unused-import]
from .location import finding_location, location_from_item  # ruff:ignore[unused-import]
from .ruff_like import is_ruff_like_item, ruff_like_finding  # ruff:ignore[unused-import]
from .utils import (  # ruff:ignore[unused-import]
    decode_json_payload,
    empty_pass_report,
    extract_items,
    findings_report,
    read_tool_output,
    tool_exit_report,
)
