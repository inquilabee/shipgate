"""Shared assertions for radon normalizer unit tests."""

from __future__ import annotations

import pytest


def assert_mi_median_p95_failure(report) -> None:
    assert report.extra["metric_median"] == pytest.approx(45.0)
    assert report.extra["metric_p95"] == pytest.approx(84.0)
    assert report.status == "failed"
    assert_has_metric_rules(
        report,
        {"median-threshold", "p95-threshold", "metric-summary", "metric-offender"},
    )
    assert_mi_offender_d_py(report)


def assert_has_metric_rules(report, expected: set[str]) -> None:
    rule_ids = {finding.rule_id for finding in report.findings}
    assert expected <= rule_ids
    summary = next(finding for finding in report.findings if finding.rule_id == "metric-summary")
    assert "n=4" in summary.message
    assert "median=45.0000" in summary.message


def assert_mi_offender_d_py(report) -> None:
    offenders = [finding for finding in report.findings if finding.rule_id == "metric-offender"]
    assert offenders[0].location is not None
    assert offenders[0].location.path == "d.py"
    assert "20.00" in offenders[0].message


def assert_cc_median_p95_failure(report) -> None:
    assert report.extra["metric_median"] == pytest.approx(2.5)
    assert report.extra["metric_p95"] == pytest.approx(17.45)
    assert report.status == "failed"
    rule_ids = [finding.rule_id for finding in report.findings]
    assert rule_ids.count("p95-threshold") == 1
    assert "metric-summary" in rule_ids
    assert "metric-offender" in rule_ids
    assert_cc_p95_ceiling_message(report)
    assert_cc_offender_app_py(report)


def assert_cc_p95_ceiling_message(report) -> None:
    assert "exceeds ceiling 10" in next(
        finding.message for finding in report.findings if finding.rule_id == "p95-threshold"
    )


def assert_cc_offender_app_py(report) -> None:
    offender = next(finding for finding in report.findings if finding.rule_id == "metric-offender")
    assert offender.location is not None
    assert offender.location.path == "src/app.py"
    assert "20.00" in offender.message
