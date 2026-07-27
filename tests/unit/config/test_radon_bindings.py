from pathlib import Path

import pytest

from shipgate.config.core import ProjectConfigParser
from shipgate.domain.project import CheckBinding
from shipgate.errors import ConfigError


def parse_checks(tmp_path: Path, checks: dict[str, object]) -> tuple[CheckBinding, ...]:
    config = ProjectConfigParser.parse(
        {"suite": "full", "env": "managed", "checks": checks},
        tmp_path / "shipgate.yaml",
    )
    return config.check_bindings


def test_parse_radon_mi_modes(tmp_path: Path):
    mi = parse_checks(
        tmp_path,
        {
            "radon.mi": {
                "threshold": "B",
                "average-mode": "progressive",
                "median-mode": "threshold",
                "median-threshold": 55,
                "p5-mode": "threshold",
                "p5-threshold": 25,
                "p10-mode": "threshold",
                "p10-threshold": 30,
                "p95-mode": "threshold",
                "p95-threshold": 80,
            },
        },
    )[0]
    assert (mi.average_mode, mi.median_mode, mi.p95_mode) == (
        "progressive",
        "threshold",
        "threshold",
    )
    assert (mi.p5_mode, mi.p10_mode) == ("threshold", "threshold")
    assert (mi.median_threshold, mi.p95_threshold) == (pytest.approx(55.0), pytest.approx(80.0))
    assert (mi.p5_threshold, mi.p10_threshold) == (pytest.approx(25.0), pytest.approx(30.0))


def test_parse_radon_mi_minimum_threshold(tmp_path: Path):
    mi = parse_checks(
        tmp_path,
        {
            "radon.mi": {
                "minimum-mode": "threshold",
                "minimum-threshold": 20,
            },
        },
    )[0]
    assert mi.minimum_mode == "threshold"
    assert mi.minimum_threshold == pytest.approx(20.0)
    assert mi.maximum_mode is None


def test_parse_radon_cc_modes(tmp_path: Path):
    cc = parse_checks(
        tmp_path,
        {
            "radon.cc": {
                "threshold": "B",
                "average-mode": "threshold",
                "average-threshold": 5.5,
                "median-mode": "threshold",
                "median-threshold": 3,
                "maximum-mode": "progressive",
                "p95-mode": "threshold",
                "p95-threshold": 8,
            },
        },
    )[0]
    assert cc.average_threshold == pytest.approx(5.5)
    assert cc.median_threshold == pytest.approx(3.0)
    assert cc.p95_threshold == pytest.approx(8.0)
    assert cc.maximum_mode == "progressive"
    assert cc.minimum_mode is None


def test_parse_metric_threshold_mode_requires_bound(tmp_path: Path):
    with pytest.raises(ConfigError, match="minimum-mode threshold requires minimum-threshold"):
        parse_checks(tmp_path, {"radon.mi": {"minimum-mode": "threshold"}})


def test_parse_metric_mode_accepts_snake_case(tmp_path: Path):
    cc = parse_checks(
        tmp_path,
        {
            "radon.cc": {
                "maximum_mode": "progressive",
                "average_mode": "threshold",
                "average_threshold": 8,
            },
        },
    )[0]
    assert cc.maximum_mode == "progressive"
    assert cc.average_mode == "threshold"
    assert cc.average_threshold == pytest.approx(8.0)
