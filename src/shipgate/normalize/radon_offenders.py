"""Emit actionable distribution findings when radon metric gates fail."""

from __future__ import annotations

from typing import TYPE_CHECKING

from shipgate.domain.reports import Finding, FindingLocation
from shipgate.normalize.radon_scores import RadonScores

if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence

    from shipgate.normalize.radon_scores import ScoredMetric


class RadonOffenders:
    """Summarize distribution and list worst MI/CC units as findings."""

    @classmethod
    def distribution_failure_findings(
        cls,
        check_id: str,
        payload: Mapping[str, object],
        metrics: Mapping[str, object],
        *,
        metric_label: str,
        is_mi: bool,
        limit: int = RadonScores.DEFAULT_OFFENDER_LIMIT,
    ) -> list[Finding]:
        findings: list[Finding] = []
        summary = cls.summary_finding(check_id, metrics)
        if summary is not None:
            findings.append(summary)
        worse_when = metrics.get("metric_worse_when")
        if worse_when not in {"higher", "lower"}:
            return findings
        items = RadonScores.mi_items(payload) if is_mi else RadonScores.cc_items(payload)
        findings.extend(
            cls.offender_findings(
                check_id,
                items,
                worse_when=str(worse_when),
                metric_label=metric_label,
                limit=limit,
            )
        )
        return findings

    @classmethod
    def summary_finding(
        cls,
        check_id: str,
        metrics: Mapping[str, object],
    ) -> Finding | None:
        count = metrics.get("metric_count")
        median = metrics.get("metric_median")
        average = metrics.get("metric_average")
        if not isinstance(count, int):
            return None
        if not isinstance(median, (int, float)) or not isinstance(average, (int, float)):
            return None
        return Finding(
            check_id=check_id,
            rule_id="metric-summary",
            severity="error",
            message=(
                f"Distribution n={count} median={float(median):.4f} mean={float(average):.4f}"
            ),
        )

    @classmethod
    def offender_findings(
        cls,
        check_id: str,
        items: Sequence[ScoredMetric],
        *,
        worse_when: str,
        metric_label: str,
        limit: int,
    ) -> list[Finding]:
        findings: list[Finding] = []
        for item in RadonScores.ranked_offenders(items, worse_when=worse_when, limit=limit):
            detail = f" ({item.detail})" if item.detail else ""
            findings.append(
                Finding(
                    check_id=check_id,
                    rule_id="metric-offender",
                    severity="error",
                    message=f"{metric_label} {item.score:.2f}{detail}",
                    location=FindingLocation(path=item.path, line=item.line),
                )
            )
        return findings
