"""Normalize package."""

from __future__ import annotations

from shipgate.core.registry import Registry
from shipgate.normalize import (
    bandit,
    gitleaks,
    jscpd,
    radon,
    ruff,
    semgrep,
    ty,
)
from shipgate.normalize.core import (
    CodespellNormalizer,
    DeadcodeNormalizer,
    GateJsonNormalizer,
    GenericExitNormalizer,
    MarkdownlintNormalizer,
    Normalizer,
    VultureNormalizer,
)

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
        "jscpd": jscpd.JscpdNormalizer(),
    },
    unknown_message="unknown normalizer: {name!r}",
)
NORMALIZERS = NORMALIZER_REGISTRY.items()


def get_normalizer(name: str) -> Normalizer:
    return NORMALIZER_REGISTRY.get(name)
