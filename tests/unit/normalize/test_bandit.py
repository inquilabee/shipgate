import json
from pathlib import Path

from shipgate.catalog.loader import load_catalog
from shipgate.domain.options import NormalizedOptions
from shipgate.normalize.bandit import BanditNormalizer


def test_bandit_normalizer_parses_results(make_resolved_request, make_process_result):
    tool = load_catalog().get_tool("bandit.scan")
    base = make_resolved_request(tool=tool)
    resolved = make_resolved_request(
        tool=tool,
        stdout_path=base.project_root / ".shipgate/reports/raw/bandit.json",
    )
    payload = {
        "results": [
            {
                "filename": "app.py",
                "line_number": 3,
                "test_id": "B101",
                "issue_severity": "HIGH",
                "issue_text": "use of assert",
            }
        ]
    }
    result = make_process_result(
        exit_code=1,
        stdout=json.dumps(payload),
    )
    report = BanditNormalizer().normalize(resolved, result)
    assert report.status == "failed"
    assert report.findings[0].rule_id == "B101"
    location = report.findings[0].location
    assert location is not None
    assert location.path == "app.py"


def test_bandit_normalizer_reads_json_from_output_file_with_progress_stdout(
    tmp_path: Path,
    make_resolved_request,
    make_process_result,
):
    tool = load_catalog().get_tool("bandit.scan")
    output_path = tmp_path / ".shipgate/reports/raw/bandit.scan.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "results": [
            {
                "filename": "app.py",
                "line_number": 3,
                "test_id": "B101",
                "issue_severity": "HIGH",
                "issue_text": "use of assert",
            }
        ]
    }
    output_path.write_text(json.dumps(payload), encoding="utf-8")
    resolved = make_resolved_request(
        tool=tool,
        stdout_path=output_path,
        options=NormalizedOptions(output=output_path, format="json"),
    )
    result = make_process_result(
        exit_code=1,
        stdout="Working... ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 100% 0:00:00\n",
        stderr="[json]\tINFO\tJSON output written to file",
    )
    report = BanditNormalizer().normalize(resolved, result)
    assert report.status == "failed"
    assert report.findings[0].rule_id == "B101"


def test_bandit_normalizer_falls_back_on_unparseable_output(
    make_resolved_request, make_process_result
):
    tool = load_catalog().get_tool("bandit.scan")
    base = make_resolved_request(tool=tool)
    resolved = make_resolved_request(
        tool=tool,
        stdout_path=base.project_root / ".shipgate/reports/raw/bandit.scan.json",
    )
    result = make_process_result(
        exit_code=2,
        stdout="not json",
        stderr="bandit: command failed",
    )
    report = BanditNormalizer().normalize(resolved, result)
    assert report.status == "failed"
    assert report.findings[0].rule_id == "TOOL_EXIT"
    assert "bandit: command failed" in report.findings[0].message
