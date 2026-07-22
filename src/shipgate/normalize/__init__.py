"""Normalize package."""

from __future__ import annotations

from typing import TYPE_CHECKING

from shipgate.core.registry import Registry
from shipgate.normalize import (
    bandit,
    gitleaks,
    radon,
    ruff,
    semgrep,
    ty,
)
from shipgate.normalize.core.exit import (
    CodespellNormalizer,
    DeadcodeNormalizer,
    MarkdownlintNormalizer,
    VultureNormalizer,
)
from shipgate.normalize.core.gate_json import GateJsonNormalizer
from shipgate.normalize.core.generic import GenericExitNormalizer

if TYPE_CHECKING:
    from shipgate.normalize.core.base import Normalizer

NORMALIZER_REGISTRY = Registry(
    {
        "ruff": ruff.RuffNormalizer(),
        "generic_exit": GenericExitNormalizer(),
        "bandit": bandit.BanditNormalizer(),
        "semgrep": semgrep.SemgrepNormalizer(),
        "codespell": CodespellNormalizer(),
        "gitleaks": gitleaks.GitleaksNormalizer(),
        "markdownlint": MarkdownlintNormalizer(),
        "ty": ty.TyNormalizer(),
        "radon": radon.RadonNormalizer(),
        "vulture": VultureNormalizer(),
        "deadcode": DeadcodeNormalizer(),
        "gate_json": GateJsonNormalizer(),
    },
    unknown_message="unknown normalizer: {name!r}",
)
NORMALIZERS = NORMALIZER_REGISTRY.items()


def get_normalizer(name: str) -> Normalizer:
    if name not in NORMALIZER_REGISTRY:
        return GenericExitNormalizer()
    return NORMALIZER_REGISTRY.get(name)
