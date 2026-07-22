"""Normalizer protocol and base class."""

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
