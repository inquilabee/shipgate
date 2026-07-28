"""Baseline comparison helpers for the report UI."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from shipgate.domain.reports import RunReport
    from shipgate.frontend.domain.models import FindingRecord


def finding_fingerprint(
    *,
    check_id: str,
    rule_id: str,
    path: str | None,
    line: int | None,
    message: str,
) -> tuple[str, str, str, int | None, str]:
    return (check_id, rule_id, path or "", line, message)


def fingerprints_from_report(
    report: RunReport,
) -> set[tuple[str, str, str, int | None, str]]:
    result: set[tuple[str, str, str, int | None, str]] = set()
    for finding in (finding for check in report.reports for finding in check.findings):
        loc = finding.location
        result.add(
            finding_fingerprint(
                check_id=finding.check_id,
                rule_id=finding.rule_id,
                path=loc.path if loc else None,
                line=loc.line if loc else None,
                message=finding.message,
            )
        )
    return result


def fingerprint_from_record(
    record: FindingRecord,
) -> tuple[str, str, str, int | None, str]:
    return finding_fingerprint(
        check_id=record.check_id,
        rule_id=record.rule_id,
        path=record.file,
        line=record.line,
        message=record.message,
    )


def fixed_fingerprints(
    baseline_fps: set[tuple[str, str, str, int | None, str]],
    current_fps: set[tuple[str, str, str, int | None, str]],
) -> set[tuple[str, str, str, int | None, str]]:
    """Fingerprints present in baseline but absent from the current run."""
    return baseline_fps - current_fps


def fixed_finding_rows(
    report: RunReport,
    fixed_fps: set[tuple[str, str, str, int | None, str]],
    *,
    limit: int = 20,
) -> list[dict[str, str | int | None]]:
    """Compact rows for baseline findings that were fixed in the current run."""
    rows: list[dict[str, str | int | None]] = []
    for finding in (finding for check in report.reports for finding in check.findings):
        loc = finding.location
        fp = finding_fingerprint(
            check_id=finding.check_id,
            rule_id=finding.rule_id,
            path=loc.path if loc else None,
            line=loc.line if loc else None,
            message=finding.message,
        )
        if fp not in fixed_fps:
            continue
        rows.append(
            {
                "check_id": finding.check_id,
                "rule_id": finding.rule_id,
                "file": loc.path if loc else None,
                "line": loc.line if loc else None,
                "message": finding.message,
            }
        )
        if len(rows) >= limit:
            return rows
    return rows


def severity_deltas_vs_baseline(
    current: dict[str, int],
    baseline: dict[str, int],
) -> dict[str, int]:
    keys = ("error", "warning", "info")
    return {key: current.get(key, 0) - baseline.get(key, 0) for key in keys}
