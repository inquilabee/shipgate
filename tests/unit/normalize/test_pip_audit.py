import json

from shipgate.catalog.loader import CatalogLoader
from shipgate.domain.options import NormalizedOptions
from shipgate.normalize.pip_audit import PipAuditNormalizer


def test_pip_audit_normalizer_flattens_vulnerabilities(make_resolved_request, make_process_result):
    tool = CatalogLoader.load().get_tool("pip-audit.audit")
    resolved = make_resolved_request(tool=tool)
    payload = {
        "dependencies": [
            {"name": "safe", "version": "1.0.0", "vulns": []},
            {
                "name": "vulnerable",
                "version": "0.1.0",
                "vulns": [
                    {
                        "id": "GHSA-xxxx",
                        "fix_versions": ["1.0.0"],
                        "aliases": ["CVE-2024-0001"],
                        "description": "example vulnerability",
                    }
                ],
            },
        ],
        "fixes": [],
    }
    result = make_process_result(exit_code=1, stdout=json.dumps(payload))
    report = PipAuditNormalizer().normalize(resolved, result)
    assert report.status == "failed"
    assert len(report.findings) == 1
    assert report.findings[0].rule_id == "GHSA-xxxx"
    assert "vulnerable" in report.findings[0].message
    assert "CVE-2024-0001" in report.findings[0].message


def test_pip_audit_normalizer_passes_when_no_vulnerabilities(
    make_resolved_request, make_process_result
):
    tool = CatalogLoader.load().get_tool("pip-audit.audit")
    resolved = make_resolved_request(tool=tool)
    payload = {
        "dependencies": [{"name": "safe", "version": "1.0.0", "vulns": []}],
        "fixes": [],
    }
    result = make_process_result(exit_code=0, stdout=json.dumps(payload))
    report = PipAuditNormalizer().normalize(resolved, result)
    assert report.status == "passed"
    assert report.findings == ()


def test_pip_audit_normalizer_reads_output_file(
    tmp_path, make_resolved_request, make_process_result
):
    tool = CatalogLoader.load().get_tool("pip-audit.audit")
    output_path = tmp_path / ".shipgate/reports/raw/pip-audit.audit.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "dependencies": [
            {
                "name": "pkg",
                "version": "1.0",
                "vulns": [{"id": "VULN-1", "description": "bad"}],
            }
        ],
        "fixes": [],
    }
    output_path.write_text(json.dumps(payload), encoding="utf-8")
    resolved = make_resolved_request(
        tool=tool,
        stdout_path=output_path,
        options=NormalizedOptions(output=output_path, format="json"),
    )
    result = make_process_result(exit_code=1, stdout="No known vulnerabilities found\n")
    report = PipAuditNormalizer().normalize(resolved, result)
    assert report.status == "failed"
    assert report.findings[0].rule_id == "VULN-1"
