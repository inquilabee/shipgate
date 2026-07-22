"""Shared indented JSON serialization."""

from __future__ import annotations

import json


def dumps_indented(payload: object, *, trailing_newline: bool = True) -> str:
    text = json.dumps(payload, indent=2)
    if trailing_newline:
        text += "\n"
    return text
