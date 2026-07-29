from pathlib import Path

import pytest
from tests.unit.support.radon import normalize_payload
from tests.unit.support.radon_assertions import assert_mi_median_p95_failure

from shipgate.normalize.radon import RadonNormalizer
from shipgate.paths import (
    RADON_MI_AVG_CACHE_ENV,
    RADON_MI_MEDIAN_CACHE_ENV,
    RADON_MI_MIN_CACHE_ENV,
    RADON_MI_P5_CACHE_ENV,
    RADON_MI_P10_CACHE_ENV,
    RADON_MI_P95_CACHE_ENV,
)


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
    assert_mi_median_p95_failure(report)


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
