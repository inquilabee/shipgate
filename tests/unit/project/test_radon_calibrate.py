from pathlib import Path

import pytest

from shipgate.project.radon_calibrate import (
    RadonCalibrationRenderer,
    RadonCalibrator,
    calibrate_radon,
)


def test_calibrate_mi_from_json_file(tmp_path: Path):
    payload = tmp_path / "mi.json"
    payload.write_text(
        '{"a.py": {"rank": "A", "mi": 90.0},'
        '"b.py": {"rank": "A", "mi": 50.0},'
        '"c.py": {"rank": "A", "mi": 40.0},'
        '"d.py": {"rank": "A", "mi": 20.0}}',
        encoding="utf-8",
    )
    text = calibrate_radon(tmp_path, kind="mi", json_path=payload, top=2)
    assert "radon.mi calibration (n=4)" in text
    assert "p5=" in text
    assert "p10=" in text
    assert "lowest 2:" in text
    assert "d.py" in text
    assert "median-mode: threshold" in text
    assert "p5-mode: threshold" in text
    assert "minimum-mode: threshold" in text


def test_calibrate_mi_yaml_only(tmp_path: Path):
    payload = tmp_path / "mi.json"
    payload.write_text('{"a.py": {"rank": "A", "mi": 55.45}}', encoding="utf-8")
    text = calibrate_radon(tmp_path, kind="mi", json_path=payload, yaml_snippet=True)
    assert text.startswith("checks:")
    assert "radon.mi:" in text
    assert "median-threshold: 55.4" in text
    assert "lowest" not in text


def test_calibrate_cc_suggestions():
    payload = {
        "src/app.py": [
            {"type": "function", "name": "a", "rank": "A", "lineno": 1, "complexity": 1},
            {"type": "function", "name": "b", "rank": "A", "lineno": 2, "complexity": 2},
            {"type": "function", "name": "c", "rank": "A", "lineno": 3, "complexity": 3},
            {"type": "function", "name": "d", "rank": "A", "lineno": 4, "complexity": 20},
        ]
    }
    calibration = RadonCalibrator.from_payload(payload, kind="cc", top=1)
    assert calibration.count == 4
    assert calibration.suggestions["p95"] == pytest.approx(17.5)
    assert calibration.suggestions["maximum"] == pytest.approx(20.0)
    assert calibration.offenders[0].path == "src/app.py"
    assert calibration.offenders[0].detail == "function d"
    yaml_text = RadonCalibrationRenderer.yaml_snippet(calibration)
    assert "radon.cc:" in yaml_text
    assert "maximum-mode: threshold" in yaml_text
    assert "minimum-mode" not in yaml_text


def test_suggest_floor_and_ceiling():
    assert RadonCalibrator.suggest_floor(55.45) == pytest.approx(55.4)
    assert RadonCalibrator.suggest_ceiling(17.45) == pytest.approx(17.5)
