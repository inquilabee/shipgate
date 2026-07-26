from pathlib import Path

import pytest

from shipgate.domain.catalog import ToolDefinition
from shipgate.domain.execution import ExecutionEnvironment, ResolvedRequest
from shipgate.domain.modes import RunMode
from shipgate.domain.options import NormalizedOptions
from shipgate.domain.reports import CheckReport
from shipgate.normalize.radon import RadonNormalizer
from shipgate.paths import (
    PROJECT_CACHE_ENV,
    RADON_CC_AVG_CACHE_ENV,
    RADON_CC_MAX_CACHE_ENV,
    RADON_CC_MEDIAN_CACHE_ENV,
    RADON_CC_P95_CACHE_ENV,
    RADON_MI_AVG_CACHE_ENV,
    RADON_MI_MEDIAN_CACHE_ENV,
    RADON_MI_MIN_CACHE_ENV,
    RADON_MI_P95_CACHE_ENV,
    parse_env_file,
)
from shipgate.runtime.executor import ProcessResult
from shipgate.runtime.progressive_average import apply_progressive_average


def resolved(
    tmp_path: Path,
    tool_id: str,
    subcommand: tuple[str, ...],
    *,
    threshold: str | None = None,
    extra: dict[str, object] | None = None,
) -> ResolvedRequest:
    tool = ToolDefinition(
        id=tool_id,
        executable="radon",
        subcommand=subcommand,
        normalizer="radon",
    )
    return ResolvedRequest(
        runnable=tool_id,
        tool=tool,
        mode=RunMode.CHECK,
        options=NormalizedOptions(
            paths=(tmp_path,),
            threshold=threshold,
            extra=dict(extra or {}),
        ),
        option_sources={},
        extra_args=(),
        project_root=tmp_path,
        output_path=tmp_path / "out.json",
        environment=ExecutionEnvironment(kind="system", root=None, env={}),
    )


def normalize_payload(
    tmp_path: Path,
    tool_id: str,
    subcommand: tuple[str, ...],
    payload: str,
    *,
    threshold: str | None = None,
    extra: dict[str, object] | None = None,
) -> CheckReport:
    return RadonNormalizer().normalize(
        resolved(tmp_path, tool_id, subcommand, threshold=threshold, extra=extra),
        ProcessResult(
            argv=(),
            cwd=tmp_path,
            exit_code=0,
            stdout=payload,
            stderr="",
            duration_ms=1,
        ),
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
    assert report.findings[0].rule_id == "average-threshold"


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
    assert {finding.rule_id for finding in report.findings} == {
        "median-threshold",
        "p95-threshold",
    }


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
    assert report.findings[0].rule_id == "minimum-threshold"
    assert "below floor 20" in report.findings[0].message


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
    assert report.findings[0].rule_id == "maximum-threshold"


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
    assert len(report.findings) == 1
    assert report.findings[0].rule_id == "p95-threshold"
    assert "exceeds ceiling 10" in report.findings[0].message


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
