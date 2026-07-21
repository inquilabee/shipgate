"""Normalizer protocol and registry."""

from typing import Protocol

from shipgate.domain.execution import ResolvedRequest
from shipgate.domain.reports import CheckReport
from shipgate.normalize import generic, radon, ruff
from shipgate.runtime.executor import ProcessResult


class Normalizer(Protocol):
    def normalize(self, request: ResolvedRequest, result: ProcessResult) -> CheckReport: ...


NORMALIZERS: dict[str, Normalizer] = {
    "ruff": ruff.RuffNormalizer(),
    "generic_exit": generic.GenericExitNormalizer(),
    "bandit": generic.GenericExitNormalizer(),
    "semgrep": generic.GenericExitNormalizer(),
    "codespell": generic.GenericExitNormalizer(),
    "gitleaks": generic.GenericExitNormalizer(),
    "markdownlint": generic.GenericExitNormalizer(),
    "ty": generic.GenericExitNormalizer(),
    "pytest": generic.GenericExitNormalizer(),
    "radon": radon.RadonNormalizer(),
    "vulture": generic.GenericExitNormalizer(),
    "deadcode": generic.GenericExitNormalizer(),
}


def get_normalizer(name: str) -> Normalizer:
    if name not in NORMALIZERS:
        return generic.GenericExitNormalizer()
    return NORMALIZERS[name]
