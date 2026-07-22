"""Normalizer protocol and registry."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from shipgate.domain.execution import ResolvedRequest
    from shipgate.domain.reports import CheckReport
    from shipgate.runtime.executor import ProcessResult


class Normalizer(Protocol):
    def normalize(self, request: ResolvedRequest, result: ProcessResult) -> CheckReport: ...


class BaseNormalizer(ABC):
    @abstractmethod
    def normalize(self, request: ResolvedRequest, result: ProcessResult) -> CheckReport: ...


from shipgate.normalize import (  # noqa: E402
    bandit,
    exit_normalizers,
    gate_json,
    generic,
    gitleaks,
    radon,
    ruff,
    semgrep,
    ty,
)

NORMALIZERS: dict[str, Normalizer] = {
    "ruff": ruff.RuffNormalizer(),
    "generic_exit": generic.GenericExitNormalizer(),
    "bandit": bandit.BanditNormalizer(),
    "semgrep": semgrep.SemgrepNormalizer(),
    "codespell": exit_normalizers.CodespellNormalizer(),
    "gitleaks": gitleaks.GitleaksNormalizer(),
    "markdownlint": exit_normalizers.MarkdownlintNormalizer(),
    "ty": ty.TyNormalizer(),
    "radon": radon.RadonNormalizer(),
    "vulture": exit_normalizers.VultureNormalizer(),
    "deadcode": exit_normalizers.DeadcodeNormalizer(),
    "gate_json": gate_json.GateJsonNormalizer(),
}


def get_normalizer(name: str) -> Normalizer:
    if name not in NORMALIZERS:
        return generic.GenericExitNormalizer()
    return NORMALIZERS[name]
