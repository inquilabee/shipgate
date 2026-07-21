from pathlib import Path

from shipgate.domain.reports import CheckReport, Finding, FindingLocation, RunReport
from shipgate.frontend.domain.models import FindingCategory
from shipgate.frontend.services.ingest import ingest_run_report
from shipgate.frontend.storage.sqlite import SqliteStorage


def test_ingest_run_report_counts_code_and_tool_findings(tmp_path: Path):
    storage = SqliteStorage(tmp_path / "report.db")
    storage.create_run(branch="main", suite_id="standard", run_id="run-1")
    report = RunReport(
        run_id="run-1",
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
                        message="unused import",
                        location=FindingLocation(path="src/app.py", line=1),
                    ),
                ),
            ),
            CheckReport(
                check_id="gitleaks.scan",
                tool_id="gitleaks.scan",
                status="failed",
                exit_code=3,
                findings=(),
            ),
        ),
    )
    summary = ingest_run_report(storage, "run-1", report, tmp_path)
    assert summary.finding_count == 1
    assert summary.tool_failure_count == 1
    assert summary.by_severity["error"] == 1
    code = storage.list_findings("run-1", category=FindingCategory.CODE)
    tool = storage.list_findings("run-1", category=FindingCategory.TOOL)
    assert len(code) == 1
    assert len(tool) == 1
    assert code[0].file == "src/app.py"
