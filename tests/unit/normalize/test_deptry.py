import json

from shipgate.catalog.loader import CatalogLoader
from shipgate.domain.options import NormalizedOptions
from shipgate.normalize.deptry import DeptryNormalizer


def test_deptry_normalizer_parses_json_array(make_resolved_request, make_process_result):
    tool = CatalogLoader.load().get_tool("deptry.check")
    resolved = make_resolved_request(tool=tool)
    payload = [
        {
            "error": {
                "code": "DEP002",
                "message": "'requests' defined as a dependency but not used in the codebase",
            },
            "module": "requests",
            "location": {"file": "pyproject.toml", "line": None, "column": None},
        }
    ]
    result = make_process_result(exit_code=1, stdout=json.dumps(payload))
    report = DeptryNormalizer().normalize(resolved, result)
    assert report.status == "failed"
    assert report.findings[0].rule_id == "DEP002"
    location = report.findings[0].location
    assert location is not None
    assert location.path == "pyproject.toml"


def test_deptry_normalizer_passes_on_empty_array(make_resolved_request, make_process_result):
    tool = CatalogLoader.load().get_tool("deptry.check")
    resolved = make_resolved_request(tool=tool)
    result = make_process_result(exit_code=0, stdout="[]")
    report = DeptryNormalizer().normalize(resolved, result)
    assert report.status == "passed"
    assert report.findings == ()


def test_deptry_normalizer_reads_json_output_file(
    tmp_path, make_resolved_request, make_process_result
):
    tool = CatalogLoader.load().get_tool("deptry.check")
    output_path = tmp_path / ".shipgate/reports/raw/deptry.check.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    payload = [
        {
            "error": {"code": "DEP001", "message": "'httpx' imported but missing"},
            "module": "httpx",
            "location": {"file": "src/app.py", "line": 2, "column": 1},
        }
    ]
    output_path.write_text(json.dumps(payload), encoding="utf-8")
    resolved = make_resolved_request(
        tool=tool,
        stdout_path=output_path,
        options=NormalizedOptions(output=output_path),
    )
    result = make_process_result(
        exit_code=1,
        stdout="Found 1 dependency issue.\n",
    )
    report = DeptryNormalizer().normalize(resolved, result)
    assert report.status == "failed"
    assert report.findings[0].rule_id == "DEP001"
    location = report.findings[0].location
    assert location is not None
    assert location.path == "src/app.py"
    assert location.line == 2
