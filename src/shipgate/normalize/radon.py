"""Radon JSON normalizer with configurable maximum allowed grade."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any, ClassVar

from shipgate.domain.reports import CheckReport, Finding, FindingLocation
from shipgate.errors import NormalizationError
from shipgate.normalize.core.base import BaseNormalizer
from shipgate.normalize.core.utils import tool_exit_report

if TYPE_CHECKING:
    from shipgate.domain.execution import ResolvedRequest
    from shipgate.runtime.executor import ProcessResult


class RadonNormalizer(BaseNormalizer):
    RANK_ORDER: ClassVar[dict[str, int]] = {
        "A": 1,
        "B": 2,
        "C": 3,
        "D": 4,
        "E": 5,
        "F": 6,
    }
    DEFAULT_MAX_COMPLEXITY_RANK: ClassVar[str] = "C"

    def normalize(self, request: ResolvedRequest, result: ProcessResult) -> CheckReport:
        check_id = request.tool.id
        payload_text = result.stdout.strip()
        if not payload_text:
            if result.exit_code == 0:
                return CheckReport(
                    check_id=check_id,
                    tool_id=check_id,
                    status="passed",
                    exit_code=0,
                )
            return tool_exit_report(check_id, result)

        try:
            payload = json.loads(payload_text)
        except json.JSONDecodeError as exc:
            raise NormalizationError(f"invalid radon JSON output: {exc}") from exc
        if not isinstance(payload, dict):
            raise NormalizationError("radon output must be a JSON object")

        max_rank = request.options.threshold or self.DEFAULT_MAX_COMPLEXITY_RANK
        max_value = self.RANK_ORDER.get(
            str(max_rank).upper(), self.RANK_ORDER[self.DEFAULT_MAX_COMPLEXITY_RANK]
        )
        if "mi" in request.tool.subcommand:
            findings = self.mi_findings(check_id, payload, max_value)
        else:
            findings = self.cc_findings(check_id, payload, max_value)

        status = "failed" if findings or result.exit_code != 0 else "passed"
        return CheckReport(
            check_id=check_id,
            tool_id=check_id,
            status=status,
            exit_code=result.exit_code,
            findings=tuple(findings),
        )

    @classmethod
    def cc_findings(cls, check_id: str, payload: dict[str, Any], max_value: int) -> list[Finding]:
        findings: list[Finding] = []
        for file_path, blocks in payload.items():
            if not isinstance(blocks, list):
                continue
            for block in blocks:
                if not isinstance(block, dict):
                    continue
                rank = str(block.get("rank", "A"))
                if cls.RANK_ORDER.get(rank, 99) <= max_value:
                    continue
                block_type = block.get("type", "block")
                name = block.get("name", "")
                findings.append(
                    Finding(
                        check_id=check_id,
                        rule_id="complexity",
                        severity="error",
                        message=f"{block_type} {name} complexity rank {rank}",
                        location=FindingLocation(
                            path=str(file_path),
                            line=block.get("lineno"),
                        ),
                    )
                )
        return findings

    @classmethod
    def mi_findings(cls, check_id: str, payload: dict[str, Any], max_value: int) -> list[Finding]:
        findings: list[Finding] = []
        for file_path, item in payload.items():
            if not isinstance(item, dict):
                continue
            rank = str(item.get("rank", "A"))
            if cls.RANK_ORDER.get(rank, 99) <= max_value:
                continue
            findings.append(
                Finding(
                    check_id=check_id,
                    rule_id="maintainability",
                    severity="error",
                    message=f"Maintainability index rank {rank} (mi={item.get('mi')})",
                    location=FindingLocation(path=str(file_path)),
                )
            )
        return findings
