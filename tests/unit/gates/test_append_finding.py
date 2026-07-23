import json
import sys

from shipgate.core import run_command
from shipgate.gates.append_finding import append_finding, main


def test_append_finding_writes_location(tmp_path):
    report_path = tmp_path / "report.json"
    report_path.write_text('{"findings":[]}\n', encoding="utf-8")

    append_finding(
        report_path,
        "line-limit",
        "error",
        "too long",
        file="src/a.py",
        line="42",
    )

    payload = json.loads(report_path.read_text(encoding="utf-8"))
    assert payload == {
        "findings": [
            {
                "rule_id": "line-limit",
                "severity": "error",
                "message": "too long",
                "location": {"file": "src/a.py", "line": 42},
            }
        ]
    }


def test_append_finding_skips_invalid_line(tmp_path):
    report_path = tmp_path / "report.json"
    report_path.write_text('{"findings":[]}\n', encoding="utf-8")

    append_finding(
        report_path,
        "line-limit",
        "error",
        "too long",
        file="src/a.py",
        line="not-a-number",
    )

    finding = json.loads(report_path.read_text(encoding="utf-8"))["findings"][0]
    assert finding["location"] == {"file": "src/a.py"}


def test_append_finding_main_cli(tmp_path):
    report_path = tmp_path / "report.json"
    report_path.write_text('{"findings":[]}\n', encoding="utf-8")

    assert (
        main(
            [
                str(report_path),
                "rule",
                "warning",
                "message",
                "src/b.py",
                "3",
            ]
        )
        == 0
    )

    payload = json.loads(report_path.read_text(encoding="utf-8"))
    assert payload["findings"][0]["severity"] == "warning"


def test_append_finding_module_invocation(tmp_path):
    report_path = tmp_path / "report.json"
    report_path.write_text('{"findings":[]}\n', encoding="utf-8")

    result = run_command(
        [
            sys.executable,
            "-m",
            "shipgate.gates.append_finding",
            str(report_path),
            "rule",
            "error",
            "failed",
        ],
    )

    assert result.returncode == 0
    payload = json.loads(report_path.read_text(encoding="utf-8"))
    assert payload["findings"][0]["message"] == "failed"
