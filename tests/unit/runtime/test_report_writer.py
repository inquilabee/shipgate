from shipgate.domain.reports import (
    SCHEMA_VERSION,
    CheckReport,
    Finding,
    FindingLocation,
    RunReport,
)
from shipgate.runtime.report_store import ReportStore
from shipgate.runtime.reports import generate_run_id


def test_schema_version_in_output():
    report = RunReport(run_id="test", suite="standard", mode="check", status="passed")
    data = report.to_dict()
    assert data["schema_version"] == SCHEMA_VERSION


def test_write_failure_report_via_store(tmp_path):
    report = RunReport(
        run_id=generate_run_id(),
        suite="standard",
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
    finalized = ReportStore(tmp_path).save_final(report)
    assert finalized.report_path is not None
    path = tmp_path / finalized.report_path
    assert path.is_file()
    assert "failures" in path.parts
