from shipgate.domain.reports import CheckReport, Finding, FindingLocation, RunReport
from shipgate.frontend.domain.baseline import (
    finding_fingerprint,
    fingerprints_from_report,
    fixed_fingerprints,
)
from shipgate.frontend.services.ingest import docs_from_extra, finding_to_record


def test_fixed_fingerprints_are_baseline_minus_current():
    baseline = {
        finding_fingerprint(
            check_id="ruff.lint", rule_id="F401", path="a.py", line=1, message="x"
        ),
        finding_fingerprint(
            check_id="ruff.lint", rule_id="F401", path="b.py", line=2, message="y"
        ),
    }
    current = {
        finding_fingerprint(
            check_id="ruff.lint", rule_id="F401", path="a.py", line=1, message="x"
        ),
    }
    fixed = fixed_fingerprints(baseline, current)
    assert len(fixed) == 1
    assert next(iter(fixed))[2] == "b.py"


def test_docs_from_extra_reads_raw_url():
    url, commands = docs_from_extra(
        {"raw": {"url": "https://docs.astral.sh/ruff/rules/unused-import/"}}
    )
    assert url == "https://docs.astral.sh/ruff/rules/unused-import/"
    assert commands == []


def test_finding_to_record_populates_docs(tmp_path):
    finding = Finding(
        check_id="ruff.lint",
        rule_id="F401",
        severity="error",
        message="unused",
        location=FindingLocation(path="a.py", line=1),
        extra={
            "docs_url": "https://example.com",
            "suggested_commands": ["ruff check --fix"],
        },
    )
    record = finding_to_record(
        finding=finding,
        run_id="r1",
        check_id="ruff.lint",
        tool_id="ruff.lint",
        project_root=tmp_path,
    )
    assert record.docs_url == "https://example.com"
    assert record.suggested_commands == ["ruff check --fix"]


def test_fingerprints_from_report_roundtrip():
    report = RunReport(
        run_id="r1",
        suite="s",
        mode="check",
        status="failed",
        reports=(
            CheckReport(
                check_id="ruff.lint",
                tool_id="ruff.lint",
                status="failed",
                exit_code=1,
                findings=(
                    Finding(
                        check_id="ruff.lint",
                        rule_id="F401",
                        severity="error",
                        message="unused",
                        location=FindingLocation(path="a.py", line=1),
                    ),
                ),
            ),
        ),
    )
    assert len(fingerprints_from_report(report)) == 1
