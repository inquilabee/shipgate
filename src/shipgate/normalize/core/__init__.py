"""Normalize framework: protocols, base classes, and shared helpers."""

from .base import BaseNormalizer, Normalizer  # noqa
from .exit import (  # noqa
    CodespellNormalizer,
    DeadcodeNormalizer,
    MarkdownlintNormalizer,
    VultureNormalizer,
)
from .gate_json import GateJsonNormalizer  # noqa
from .generic import GenericExitNormalizer  # noqa
from .json import JsonItemsNormalizer  # noqa
from .location import finding_location, location_from_item  # noqa
from .ruff_like import is_ruff_like_item, ruff_like_finding  # noqa
from .utils import (  # noqa
    decode_json_payload,
    empty_pass_report,
    extract_items,
    findings_report,
    read_tool_output,
    tool_exit_report,
)
