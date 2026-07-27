from pathlib import Path

from tests.unit.support.radon import resolved

from shipgate.domain.reports import CheckReport
from shipgate.paths import (
    PROJECT_CACHE_ENV,
    RADON_CC_AVG_CACHE_ENV,
    RADON_CC_MAX_CACHE_ENV,
    RADON_MI_AVG_CACHE_ENV,
    RADON_MI_MEDIAN_CACHE_ENV,
    RADON_MI_MIN_CACHE_ENV,
    RADON_MI_P5_CACHE_ENV,
    RADON_MI_P10_CACHE_ENV,
    RADON_MI_P95_CACHE_ENV,
    parse_env_file,
)
from shipgate.runtime.progressive_average import apply_progressive_average


def test_progressive_p5_and_p10(tmp_path: Path):
    env_path = tmp_path / PROJECT_CACHE_ENV
    env_path.parent.mkdir(parents=True)
    env_path.write_text(
        f"{RADON_MI_P5_CACHE_ENV}=30.0000\n{RADON_MI_P10_CACHE_ENV}=40.0000\n",
        encoding="utf-8",
    )
    request = resolved(
        tmp_path,
        "radon.mi",
        ("mi", "-j"),
        extra={"p5_mode": "progressive", "p10_mode": "progressive"},
    )
    report = CheckReport(
        check_id="radon.mi",
        tool_id="radon.mi",
        status="passed",
        exit_code=0,
        extra={
            "metric_p5": 25.0,
            "metric_p10": 35.0,
            "metric_worse_when": "lower",
            "metric_p5_cache_key": RADON_MI_P5_CACHE_ENV,
            "metric_p10_cache_key": RADON_MI_P10_CACHE_ENV,
        },
    )
    out = apply_progressive_average(request, report)
    assert out.status == "failed"
    assert {finding.rule_id for finding in out.findings} == {
        "p5-progressive",
        "p10-progressive",
    }


def test_progressive_seeds_missing_baseline(tmp_path: Path):
    request = resolved(
        tmp_path,
        "radon.mi",
        ("mi", "-j"),
        extra={"average_mode": "progressive", "minimum_mode": "progressive"},
    )
    report = CheckReport(
        check_id="radon.mi",
        tool_id="radon.mi",
        status="passed",
        exit_code=0,
        extra={
            "metric_average": 63.62,
            "metric_extreme": 24.16,
            "metric_extreme_kind": "minimum",
            "metric_worse_when": "lower",
            "metric_average_cache_key": RADON_MI_AVG_CACHE_ENV,
            "metric_extreme_cache_key": RADON_MI_MIN_CACHE_ENV,
        },
    )
    out = apply_progressive_average(request, report)
    assert out.status == "passed"
    values = parse_env_file(tmp_path / PROJECT_CACHE_ENV)
    assert values[RADON_MI_AVG_CACHE_ENV] == "63.6200"
    assert values[RADON_MI_MIN_CACHE_ENV] == "24.1600"


def test_progressive_fails_on_regression_and_skips_update(tmp_path: Path):
    env_path = tmp_path / PROJECT_CACHE_ENV
    env_path.parent.mkdir(parents=True)
    env_path.write_text(
        f"{RADON_MI_AVG_CACHE_ENV}=70.0000\n{RADON_MI_MIN_CACHE_ENV}=30.0000\n",
        encoding="utf-8",
    )
    request = resolved(
        tmp_path,
        "radon.mi",
        ("mi", "-j"),
        extra={"average_mode": "progressive", "minimum_mode": "progressive"},
    )
    report = CheckReport(
        check_id="radon.mi",
        tool_id="radon.mi",
        status="passed",
        exit_code=0,
        extra={
            "metric_average": 63.62,
            "metric_extreme": 24.16,
            "metric_extreme_kind": "minimum",
            "metric_worse_when": "lower",
            "metric_average_cache_key": RADON_MI_AVG_CACHE_ENV,
            "metric_extreme_cache_key": RADON_MI_MIN_CACHE_ENV,
        },
    )
    out = apply_progressive_average(request, report)
    assert out.status == "failed"
    assert {finding.rule_id for finding in out.findings} == {
        "average-progressive",
        "minimum-progressive",
    }
    values = parse_env_file(env_path)
    assert values[RADON_MI_AVG_CACHE_ENV] == "70.0000"
    assert values[RADON_MI_MIN_CACHE_ENV] == "30.0000"


def test_progressive_updates_only_non_regressed_metric(tmp_path: Path):
    env_path = tmp_path / PROJECT_CACHE_ENV
    env_path.parent.mkdir(parents=True)
    env_path.write_text(
        f"{RADON_CC_AVG_CACHE_ENV}=5.0000\n{RADON_CC_MAX_CACHE_ENV}=8.0000\n",
        encoding="utf-8",
    )
    request = resolved(
        tmp_path,
        "radon.cc",
        ("cc", "-j"),
        extra={"average_mode": "progressive", "maximum_mode": "progressive"},
    )
    report = CheckReport(
        check_id="radon.cc",
        tool_id="radon.cc",
        status="passed",
        exit_code=0,
        extra={
            "metric_average": 4.5,
            "metric_extreme": 12.0,
            "metric_extreme_kind": "maximum",
            "metric_worse_when": "higher",
            "metric_average_cache_key": RADON_CC_AVG_CACHE_ENV,
            "metric_extreme_cache_key": RADON_CC_MAX_CACHE_ENV,
        },
    )
    out = apply_progressive_average(request, report)
    assert out.status == "failed"
    assert len(out.findings) == 1
    assert out.findings[0].rule_id == "maximum-progressive"
    values = parse_env_file(env_path)
    assert values[RADON_CC_AVG_CACHE_ENV] == "4.5000"
    assert values[RADON_CC_MAX_CACHE_ENV] == "8.0000"


def test_progressive_median_and_p95(tmp_path: Path):
    env_path = tmp_path / PROJECT_CACHE_ENV
    env_path.parent.mkdir(parents=True)
    env_path.write_text(
        f"{RADON_MI_MEDIAN_CACHE_ENV}=60.0000\n{RADON_MI_P95_CACHE_ENV}=90.0000\n",
        encoding="utf-8",
    )
    request = resolved(
        tmp_path,
        "radon.mi",
        ("mi", "-j"),
        extra={"median_mode": "progressive", "p95_mode": "progressive"},
    )
    report = CheckReport(
        check_id="radon.mi",
        tool_id="radon.mi",
        status="passed",
        exit_code=0,
        extra={
            "metric_median": 56.87,
            "metric_p95": 88.0,
            "metric_worse_when": "lower",
            "metric_median_cache_key": RADON_MI_MEDIAN_CACHE_ENV,
            "metric_p95_cache_key": RADON_MI_P95_CACHE_ENV,
        },
    )
    out = apply_progressive_average(request, report)
    assert out.status == "failed"
    assert {finding.rule_id for finding in out.findings} == {
        "median-progressive",
        "p95-progressive",
    }
    values = parse_env_file(env_path)
    assert values[RADON_MI_MEDIAN_CACHE_ENV] == "60.0000"
    assert values[RADON_MI_P95_CACHE_ENV] == "90.0000"
