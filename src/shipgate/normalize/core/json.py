"""JSON normalizer base implementation."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any, ClassVar

from shipgate.domain.reports import CheckReport, Finding
from shipgate.normalize.core.base import BaseNormalizer
from shipgate.normalize.core.utils import (
    decode_json_payload,
    empty_pass_report,
    extract_items,
    findings_report,
    read_tool_output,
)

if TYPE_CHECKING:
    from shipgate.domain.execution import ResolvedRequest
    from shipgate.runtime.executor import ProcessResult


class JsonItemsNormalizer(BaseNormalizer, ABC):
    """Base class for normalizers with a JSON array or keyed items payload."""

    items_key: ClassVar[str | None] = "results"
    invalid_message: ClassVar[str] = "invalid JSON output"
    decode_error: ClassVar[str | None] = None
    allow_empty_on_success: ClassVar[bool] = False

    @abstractmethod
    def item_to_finding(self, item: dict[str, Any], check_id: str) -> Finding: ...

    def parse_items(self, payload: object) -> list[dict[str, Any]]:
        return extract_items(
            payload,
            items_key=self.items_key,
            invalid_message=self.invalid_message,
        )

    def normalize(self, request: ResolvedRequest, result: ProcessResult) -> CheckReport:
        check_id = request.tool.id
        stdout = read_tool_output(request, result)
        if result.exit_code == 0 and not stdout.strip():
            return empty_pass_report(check_id)
        payload = decode_json_payload(
            stdout,
            check_id=check_id,
            result=result,
            items_key=self.items_key,
            decode_error=self.decode_error,
            allow_empty_on_success=self.allow_empty_on_success,
        )
        if isinstance(payload, CheckReport):
            return payload
        items = self.parse_items(payload)
        findings = tuple(self.item_to_finding(item, check_id) for item in items)
        return findings_report(check_id, result, findings)
