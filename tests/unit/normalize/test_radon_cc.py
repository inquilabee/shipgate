from pathlib import Path

import pytest
from tests.unit.support.radon import normalize_payload
from tests.unit.support.radon_assertions import assert_cc_median_p95_failure

from shipgate.paths import (
    RADON_CC_AVG_CACHE_ENV,
    RADON_CC_MAX_CACHE_ENV,
    RADON_CC_MEDIAN_CACHE_ENV,
    RADON_CC_P95_CACHE_ENV,
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
    assert_cc_median_p95_failure(report)
