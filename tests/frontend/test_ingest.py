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


def test_ingest_jscpd_tool_exit_threshold_message_is_code(tmp_path: Path):
    """Legacy mis-normalized threshold exits must not land in Tools that could not run."""
    storage = SqliteStorage(tmp_path / "report.db")
    storage.create_run(branch="main", suite_id="full", run_id="run-jscpd-legacy")
    finding = Finding(
        check_id="jscpd.check.python",
        rule_id="TOOL_EXIT",
        severity="error",
        message=(
            "Using config from .shipgate/configs/jscpd.python.json\n"
            "ERROR: jscpd found too many duplicates (2.4%) over threshold (2.0%)"
        ),
    )
    assert not is_tool_failure(finding)
    report = RunReport(
        run_id="run-jscpd-legacy",
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
    summary = ingest_run_report(storage, "run-jscpd-legacy", report, tmp_path)
    assert summary.tool_failure_count == 0
    assert summary.finding_count == 1
    assert storage.list_findings("run-jscpd-legacy", category=FindingCategory.TOOL) == []


def tool_finding_record(
    *,
    finding_id: str,
    run_id: str,
    check_id: str,
    message: str,
) -> FindingRecord:
    return FindingRecord(
        id=finding_id,
        run_id=run_id,
        check_id=check_id,
        tool_id=check_id.split(".", 1)[0],
        rule_id="TOOL_EXIT",
        severity="error",
        message=message,
        category=FindingCategory.TOOL,
    )


def test_repair_misclassified_jscpd_threshold_tool_findings(tmp_path: Path):
    from shipgate.frontend.domain.models import RunSummaryRecord
    from shipgate.frontend.services.ingest import repair_misclassified_tool_findings

    storage = SqliteStorage(tmp_path / "report.db")
    storage.create_run(branch="main", suite_id="full", run_id="run-old")
    storage.replace_findings(
        "run-old",
        [
            tool_finding_record(
                finding_id="f1",
                run_id="run-old",
                check_id="jscpd.check.python",
                message=(
                    "Using config from .shipgate/configs/jscpd.python.json\n"
                    "ERROR: jscpd found too many duplicates (2.4%) over threshold (2.0%)"
                ),
            ),
            tool_finding_record(
                finding_id="f2",
                run_id="run-old",
                check_id="gitleaks.scan",
                message="executable not found: gitleaks",
            ),
        ],
    )
    storage.update_run(
        "run-old",
        summary=RunSummaryRecord(
            finding_count=0,
            tool_failure_count=2,
            by_check_status={"jscpd.check.python": "failed", "gitleaks.scan": "failed"},
        ),
    )
    assert repair_misclassified_tool_findings(storage) == 1
    code = storage.list_findings("run-old", category=FindingCategory.CODE)
    tool = storage.list_findings("run-old", category=FindingCategory.TOOL)
    assert len(code) == 1
    assert "too many duplicates" in code[0].message
    assert [item.check_id for item in tool] == ["gitleaks.scan"]
    run = storage.get_run("run-old")
    assert run is not None
    assert run.summary is not None
    assert run.summary.finding_count == 1
    assert run.summary.tool_failure_count == 1


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
