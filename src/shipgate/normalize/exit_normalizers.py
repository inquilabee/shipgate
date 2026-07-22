"""Exit-code normalizers for tools without structured JSON output."""

from __future__ import annotations

from shipgate.normalize.generic import GenericExitNormalizer


class CodespellNormalizer(GenericExitNormalizer):
    """Codespell exit-code normalizer."""


class MarkdownlintNormalizer(GenericExitNormalizer):
    """Markdownlint exit-code normalizer."""


class VultureNormalizer(GenericExitNormalizer):
    """Vulture exit-code normalizer."""


class DeadcodeNormalizer(GenericExitNormalizer):
    """Deadcode exit-code normalizer."""


class PytestNormalizer(GenericExitNormalizer):
    """Pytest exit-code normalizer."""
