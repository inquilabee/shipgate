from pathlib import Path

from shipgate.domain.reports import CheckReport, Finding, FindingLocation, RunReport
from shipgate.frontend.domain.finding_context import source_contexts
from shipgate.frontend.domain.models import FindingCategory, FindingRecord
from shipgate.frontend.services.ingest import ingest_run_report, is_tool_failure
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


def test_ingest_jscpd_threshold_as_code_not_tool_failure(tmp_path: Path):
    storage = SqliteStorage(tmp_path / "report.db")
    storage.create_run(branch="main", suite_id="full", run_id="run-jscpd")
    finding = Finding(
        check_id="jscpd.check.python",
        rule_id="threshold",
        severity="error",
        message="ERROR: jscpd found too many duplicates (2.4%) over threshold (2.0%)",
    )
    assert not is_tool_failure(finding)
    report = RunReport(
        run_id="run-jscpd",
        suite="full",
        mode="check",
        status="failed",
        reports=(
            CheckReport(
                check_id="jscpd.check.python",
                tool_id="jscpd.check.python",
                status="failed",
                exit_code=1,
                findings=(finding,),
            ),
        ),
    )
    summary = ingest_run_report(storage, "run-jscpd", report, tmp_path)
    assert summary.finding_count == 1
    assert summary.tool_failure_count == 0
    code = storage.list_findings("run-jscpd", category=FindingCategory.CODE)
    assert len(code) == 1
    assert code[0].rule_id == "threshold"
    assert storage.list_findings("run-jscpd", category=FindingCategory.TOOL) == []


def test_source_context_reads_snippet(tmp_path: Path):
    source = tmp_path / "src"
    source.mkdir()
    file_path = source / "app.py"
    lines = [f"line {index}" for index in range(1, 11)]
    file_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    finding = FindingRecord(
        id="f1",
        run_id="run-1",
        check_id="ruff.lint",
        tool_id="ruff.lint",
        rule_id="F401",
        severity="error",
        message="unused import",
        file="src/app.py",
        line=5,
        category=FindingCategory.CODE,
    )
    contexts = source_contexts(tmp_path, [finding])
    assert "f1" in contexts
    snippet = contexts["f1"]
    numbers = [line.number for line in snippet.lines]
    assert 5 in numbers
    assert any(line.highlighted for line in snippet.lines)
