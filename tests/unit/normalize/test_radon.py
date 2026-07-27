from pathlib import Path

import pytest
from tests.unit.support.radon import normalize_payload

from shipgate.normalize.radon import RadonNormalizer
from shipgate.paths import (
    RADON_CC_AVG_CACHE_ENV,
    RADON_CC_MAX_CACHE_ENV,
    RADON_CC_MEDIAN_CACHE_ENV,
    RADON_CC_P95_CACHE_ENV,
    RADON_MI_AVG_CACHE_ENV,
    RADON_MI_MEDIAN_CACHE_ENV,
    RADON_MI_MIN_CACHE_ENV,
    RADON_MI_P5_CACHE_ENV,
    RADON_MI_P10_CACHE_ENV,
    RADON_MI_P95_CACHE_ENV,
)


def test_radon_cc_allows_rank_a(tmp_path: Path):
    payload = '{"src/app.py": [{"type": "function", "name": "ok", "rank": "A", "lineno": 1}]}'
    report = normalize_payload(tmp_path, "radon.cc", ("cc", "-j"), payload)
    assert report.status == "passed"
    assert report.findings == ()


def test_radon_cc_allows_rank_b(tmp_path: Path):
    payload = '{"src/app.py": [{"type": "function", "name": "ok", "rank": "B", "lineno": 10}]}'
    report = normalize_payload(tmp_path, "radon.cc", ("cc", "-j"), payload)
    assert report.status == "passed"


def test_radon_cc_allows_rank_c(tmp_path: Path):
    payload = '{"src/app.py": [{"type": "function", "name": "ok", "rank": "C", "lineno": 10}]}'
    report = normalize_payload(tmp_path, "radon.cc", ("cc", "-j"), payload)
    assert report.status == "passed"


def test_radon_cc_fails_rank_c_with_threshold_b(tmp_path: Path):
    payload = '{"src/app.py": [{"type": "function", "name": "ok", "rank": "C", "lineno": 10}]}'
    report = normalize_payload(tmp_path, "radon.cc", ("cc", "-j"), payload, threshold="B")
    assert report.status == "failed"
    assert report.findings[0].rule_id == "complexity"


def test_radon_cc_fails_rank_d(tmp_path: Path):
    payload = '{"src/app.py": [{"type": "function", "name": "bad", "rank": "D", "lineno": 10}]}'
    report = normalize_payload(tmp_path, "radon.cc", ("cc", "-j"), payload)
    assert report.status == "failed"
    assert len(report.findings) == 1
    assert report.findings[0].rule_id == "complexity"
    assert "rank D" in report.findings[0].message


def test_radon_mi_fails_rank_below_c(tmp_path: Path):
    payload = '{"src/app.py": {"rank": "D", "mi": 12.5}}'
    report = normalize_payload(tmp_path, "radon.mi", ("mi", "-j"), payload)
    assert report.status == "failed"
    assert report.findings[0].rule_id == "maintainability"


def test_radon_mi_metrics_values(tmp_path: Path):
    payload = '{"a.py": {"rank": "A", "mi": 80.0}, "b.py": {"rank": "A", "mi": 20.0}}'
    report = normalize_payload(tmp_path, "radon.mi", ("mi", "-j"), payload)
    assert report.extra["metric_average"] == pytest.approx(50.0)
    assert report.extra["metric_median"] == pytest.approx(50.0)
    assert report.extra["metric_extreme"] == pytest.approx(20.0)
    assert report.extra["metric_extreme_kind"] == "minimum"
    assert report.extra["metric_p95"] == pytest.approx(77.0)


def test_radon_mi_metric_cache_keys(tmp_path: Path):
    payload = '{"a.py": {"rank": "A", "mi": 80.0}, "b.py": {"rank": "A", "mi": 20.0}}'
    report = normalize_payload(tmp_path, "radon.mi", ("mi", "-j"), payload)
    assert report.extra["metric_average_cache_key"] == RADON_MI_AVG_CACHE_ENV
    assert report.extra["metric_median_cache_key"] == RADON_MI_MEDIAN_CACHE_ENV
    assert report.extra["metric_extreme_cache_key"] == RADON_MI_MIN_CACHE_ENV
    assert report.extra["metric_p95_cache_key"] == RADON_MI_P95_CACHE_ENV


def test_radon_mi_average_threshold_fails(tmp_path: Path):
    payload = '{"a.py": {"rank": "A", "mi": 80.0}, "b.py": {"rank": "A", "mi": 20.0}}'
    report = normalize_payload(
        tmp_path,
        "radon.mi",
        ("mi", "-j"),
        payload,
        extra={"average_mode": "threshold", "average_threshold": 60},
    )
    assert report.status == "failed"
    assert any(finding.rule_id == "average-threshold" for finding in report.findings)


def test_radon_percentile_linear_interpolation():
    assert RadonNormalizer.percentile([10.0], 95.0) == pytest.approx(10.0)
    assert RadonNormalizer.percentile([0.0, 100.0], 95.0) == pytest.approx(95.0)
    assert RadonNormalizer.percentile([10.0, 20.0, 30.0, 40.0], 95.0) == pytest.approx(38.5)


def test_radon_mi_median_p95_threshold_fails(tmp_path: Path):
    payload = (
        '{"a.py": {"rank": "A", "mi": 90.0},'
        '"b.py": {"rank": "A", "mi": 50.0},'
        '"c.py": {"rank": "A", "mi": 40.0},'
        '"d.py": {"rank": "A", "mi": 20.0}}'
    )
    report = normalize_payload(
        tmp_path,
        "radon.mi",
        ("mi", "-j"),
        payload,
        extra={
            "median_mode": "threshold",
            "median_threshold": 50,
            "p95_mode": "threshold",
            "p95_threshold": 90,
        },
    )
    assert report.extra["metric_median"] == pytest.approx(45.0)
    assert report.extra["metric_p95"] == pytest.approx(84.0)
    assert report.status == "failed"
    rule_ids = {finding.rule_id for finding in report.findings}
    assert {"median-threshold", "p95-threshold", "metric-summary", "metric-offender"} <= rule_ids
    summary = next(finding for finding in report.findings if finding.rule_id == "metric-summary")
    assert "n=4" in summary.message
    assert "median=45.0000" in summary.message
    offenders = [finding for finding in report.findings if finding.rule_id == "metric-offender"]
    assert offenders[0].location is not None
    assert offenders[0].location.path == "d.py"
    assert "20.00" in offenders[0].message


def test_radon_mi_p5_p10_threshold_fails(tmp_path: Path):
    payload = (
        '{"a.py": {"rank": "A", "mi": 90.0},'
        '"b.py": {"rank": "A", "mi": 50.0},'
        '"c.py": {"rank": "A", "mi": 40.0},'
        '"d.py": {"rank": "A", "mi": 20.0}}'
    )
    report = normalize_payload(
        tmp_path,
        "radon.mi",
        ("mi", "-j"),
        payload,
        extra={
            "p5_mode": "threshold",
            "p5_threshold": 30,
            "p10_mode": "threshold",
            "p10_threshold": 35,
        },
    )
    assert report.extra["metric_p5"] == pytest.approx(23.0)
    assert report.extra["metric_p10"] == pytest.approx(26.0)
    assert report.status == "failed"
    assert {finding.rule_id for finding in report.findings} >= {
        "p5-threshold",
        "p10-threshold",
        "metric-summary",
        "metric-offender",
    }


def test_radon_mi_p5_p10_metric_cache_keys(tmp_path: Path):
    payload = '{"a.py": {"rank": "A", "mi": 80.0}, "b.py": {"rank": "A", "mi": 20.0}}'
    report = normalize_payload(tmp_path, "radon.mi", ("mi", "-j"), payload)
    assert report.extra["metric_p5_cache_key"] == RADON_MI_P5_CACHE_ENV
    assert report.extra["metric_p10_cache_key"] == RADON_MI_P10_CACHE_ENV
    assert report.extra["metric_p5"] == pytest.approx(23.0)
    assert report.extra["metric_p10"] == pytest.approx(26.0)


def test_radon_mi_median_p95_threshold_passes(tmp_path: Path):
    payload = (
        '{"a.py": {"rank": "A", "mi": 90.0},'
        '"b.py": {"rank": "A", "mi": 50.0},'
        '"c.py": {"rank": "A", "mi": 40.0},'
        '"d.py": {"rank": "A", "mi": 20.0}}'
    )
    report = normalize_payload(
        tmp_path,
        "radon.mi",
        ("mi", "-j"),
        payload,
        extra={
            "median_mode": "threshold",
            "median_threshold": 45,
            "p95_mode": "threshold",
            "p95_threshold": 84,
        },
    )
    assert report.status == "passed"
    assert report.findings == ()


def test_radon_mi_minimum_threshold(tmp_path: Path):
    payload = '{"a.py": {"rank": "A", "mi": 80.0}, "b.py": {"rank": "A", "mi": 18.0}}'
    report = normalize_payload(
        tmp_path,
        "radon.mi",
        ("mi", "-j"),
        payload,
        extra={"minimum_mode": "threshold", "minimum_threshold": 20},
    )
    assert report.status == "failed"
    assert any(finding.rule_id == "minimum-threshold" for finding in report.findings)
    assert any("below floor 20" in finding.message for finding in report.findings)
    assert any(finding.rule_id == "metric-offender" for finding in report.findings)


def test_radon_cc_metrics_values(tmp_path: Path):
    payload = (
        '{"src/app.py": ['
        '{"type": "function", "name": "a", "rank": "A", "lineno": 1, "complexity": 2},'
        '{"type": "function", "name": "b", "rank": "A", "lineno": 10, "complexity": 12}'
        "]}"
    )
    report = normalize_payload(tmp_path, "radon.cc", ("cc", "-j"), payload)
    assert report.extra["metric_average"] == pytest.approx(7.0)
    assert report.extra["metric_median"] == pytest.approx(7.0)
    assert report.extra["metric_extreme"] == pytest.approx(12.0)
    assert report.extra["metric_extreme_kind"] == "maximum"
    assert report.extra["metric_p95"] == pytest.approx(11.5)


def test_radon_cc_metric_cache_keys(tmp_path: Path):
    payload = (
        '{"src/app.py": ['
        '{"type": "function", "name": "a", "rank": "A", "lineno": 1, "complexity": 2},'
        '{"type": "function", "name": "b", "rank": "A", "lineno": 10, "complexity": 12}'
        "]}"
    )
    report = normalize_payload(tmp_path, "radon.cc", ("cc", "-j"), payload)
    assert report.extra["metric_average_cache_key"] == RADON_CC_AVG_CACHE_ENV
    assert report.extra["metric_median_cache_key"] == RADON_CC_MEDIAN_CACHE_ENV
    assert report.extra["metric_extreme_cache_key"] == RADON_CC_MAX_CACHE_ENV
    assert report.extra["metric_p95_cache_key"] == RADON_CC_P95_CACHE_ENV


def test_radon_cc_maximum_threshold_fails(tmp_path: Path):
    payload = (
        '{"src/app.py": ['
        '{"type": "function", "name": "a", "rank": "A", "lineno": 1, "complexity": 2},'
        '{"type": "function", "name": "b", "rank": "A", "lineno": 10, "complexity": 12}'
        "]}"
    )
    report = normalize_payload(
        tmp_path,
        "radon.cc",
        ("cc", "-j"),
        payload,
        extra={"maximum_mode": "threshold", "maximum_threshold": 10},
    )
    assert report.status == "failed"
    assert any(finding.rule_id == "maximum-threshold" for finding in report.findings)


def test_radon_cc_median_and_p95_threshold(tmp_path: Path):
    payload = (
        '{"src/app.py": ['
        '{"type": "function", "name": "a", "rank": "A", "lineno": 1, "complexity": 1},'
        '{"type": "function", "name": "b", "rank": "A", "lineno": 2, "complexity": 2},'
        '{"type": "function", "name": "c", "rank": "A", "lineno": 3, "complexity": 3},'
        '{"type": "function", "name": "d", "rank": "A", "lineno": 4, "complexity": 20}'
        "]}"
    )
    report = normalize_payload(
        tmp_path,
        "radon.cc",
        ("cc", "-j"),
        payload,
        extra={
            "median_mode": "threshold",
            "median_threshold": 2.5,
            "p95_mode": "threshold",
            "p95_threshold": 10,
        },
    )
    assert report.extra["metric_median"] == pytest.approx(2.5)
    assert report.extra["metric_p95"] == pytest.approx(17.45)
    assert report.status == "failed"
    rule_ids = [finding.rule_id for finding in report.findings]
    assert rule_ids.count("p95-threshold") == 1
    assert "metric-summary" in rule_ids
    assert "metric-offender" in rule_ids
    assert "exceeds ceiling 10" in next(
        finding.message for finding in report.findings if finding.rule_id == "p95-threshold"
    )
    offender = next(finding for finding in report.findings if finding.rule_id == "metric-offender")
    assert offender.location is not None
    assert offender.location.path == "src/app.py"
    assert "20.00" in offender.message
