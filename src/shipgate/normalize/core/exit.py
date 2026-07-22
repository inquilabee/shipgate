"""Exit-code normalizers for tools without structured JSON output."""

from __future__ import annotations

from shipgate.normalize.core.generic import GenericExitNormalizer

CodespellNormalizer = GenericExitNormalizer
MarkdownlintNormalizer = GenericExitNormalizer
VultureNormalizer = GenericExitNormalizer
DeadcodeNormalizer = GenericExitNormalizer
