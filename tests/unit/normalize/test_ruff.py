import json

from shipgate.normalize.ruff import RuffNormalizer


def test_empty_list_passed(make_resolved_request, make_process_result):
    request = make_resolved_request(tool_id="ruff.lint", executable="ruff")
    result = make_process_result(stdout="[]")
    report = RuffNormalizer().normalize(request, result)
    assert report.status == "passed"


def test_one_finding_maps(make_resolved_request, make_process_result):
    request = make_resolved_request(tool_id="ruff.lint", executable="ruff")
    payload = [
        {
            "code": "F401",
            "message": "Unused import",
            "filename": "src/main.py",
            "location": {"row": 12, "column": 5},
        }
    ]
    result = make_process_result(
        exit_code=1,
        stdout=json.dumps(payload),
    )
    report = RuffNormalizer().normalize(request, result)
    assert len(report.findings) == 1
    f = report.findings[0]
    assert f.rule_id == "F401"
    assert f.location is not None
    assert f.location.line == 12
