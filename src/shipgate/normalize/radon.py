"""Radon JSON normalizer with letter-rank and optional metric gates."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, ClassVar

from shipgate.domain.reports import CheckReport, Finding, FindingLocation
from shipgate.errors import NormalizationError
from shipgate.normalize.core import BaseNormalizer, tool_exit_report
from shipgate.normalize.radon_metrics import RadonMetrics
from shipgate.normalize.radon_offenders import RadonOffenders

if TYPE_CHECKING:
    from collections.abc import Mapping

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
        is_mi = "mi" in request.tool.subcommand
        if is_mi:
            findings = self.mi_findings(check_id, payload, max_value)
            metrics = RadonMetrics.mi_metrics(payload)
            metric_label = "maintainability index"
        else:
            findings = self.cc_findings(check_id, payload, max_value)
            metrics = RadonMetrics.cc_metrics(payload)
            metric_label = "cyclomatic complexity"

        metric_findings = RadonMetrics.absolute_threshold_findings(
            check_id,
            metrics,
            request.options.extra,
            metric_label=metric_label,
        )
        findings.extend(metric_findings)
        if metric_findings:
            findings.extend(
                RadonOffenders.distribution_failure_findings(
                    check_id,
                    payload,
                    metrics,
                    metric_label=metric_label,
                    is_mi=is_mi,
                )
            )

        status = "failed" if findings or result.exit_code != 0 else "passed"
        return CheckReport(
            check_id=check_id,
            tool_id=check_id,
            status=status,
            exit_code=result.exit_code,
            findings=tuple(findings),
            extra=metrics,
        )

    @classmethod
    def cc_findings(
        cls,
        check_id: str,
        payload: Mapping[str, object],
        max_value: int,
    ) -> list[Finding]:
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
                lineno = block.get("lineno")
                findings.append(
                    Finding(
                        check_id=check_id,
                        rule_id="complexity",
                        severity="error",
                        message=f"{block_type} {name} complexity rank {rank}",
                        location=FindingLocation(
                            path=str(file_path),
                            line=lineno if isinstance(lineno, int) else None,
                        ),
                    )
                )
        return findings

    @classmethod
    def mi_findings(
        cls,
        check_id: str,
        payload: Mapping[str, object],
        max_value: int,
    ) -> list[Finding]:
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

    # Re-export metric helpers so existing tests keep a stable import surface.
    percentile = staticmethod(RadonMetrics.percentile)
    cc_complexity_values = staticmethod(RadonMetrics.cc_complexity_values)
    mi_values = staticmethod(RadonMetrics.mi_values)
