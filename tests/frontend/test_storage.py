from pathlib import Path

from shipgate.frontend.domain.models import FindingCategory, FindingRecord, RunStatus
from shipgate.frontend.storage.sqlite import SqliteStorage


def code_finding(run_id: str, *, file: str, severity: str = "error") -> FindingRecord:
    return FindingRecord(
        id=f"{file}-{severity}",
        run_id=run_id,
        check_id="ruff.lint",
        tool_id="ruff.lint",
        rule_id="F401",
        severity=severity,
        message="issue",
        file=file,
        line=1,
        category=FindingCategory.CODE,
    )


def test_storage_filters_and_pagination(tmp_path: Path):
    storage = SqliteStorage(tmp_path / "report.db")
    run = storage.create_run(branch="main", suite_id="standard", run_id="run-1")
    storage.replace_findings(
        "run-1",
        [
            code_finding("run-1", file="src/a.py", severity="error"),
            code_finding("run-1", file="src/b.py", severity="warning"),
            FindingRecord(
                id="tool-1",
                run_id="run-1",
                check_id="gitleaks.scan",
                tool_id="gitleaks.scan",
                rule_id="setup",
                severity="error",
                message="missing binary",
                category=FindingCategory.TOOL,
            ),
        ],
    )
    assert storage.count_findings("run-1", category=FindingCategory.CODE) == 2
    assert storage.count_findings("run-1", severity="error", category=FindingCategory.CODE) == 1
    page = storage.list_findings("run-1", category=FindingCategory.CODE, limit=1, offset=0)
    assert len(page) == 1
    storage.update_run(run.id, status=RunStatus.SUCCEEDED, finished=True)
    run2 = storage.create_run(branch="main", suite_id="standard", run_id="run-2")
    storage.update_run(run2.id, status=RunStatus.SUCCEEDED, finished=True)
    previous = storage.previous_completed_run(branch="main", before_run_id=run2.id)
    assert previous is not None
    assert previous.id == run.id
