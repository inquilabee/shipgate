"""Shared seed helpers for report UI TestClient and Playwright fixtures."""

from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from shipgate.baseline import save_baseline
from shipgate.domain.reports import CheckReport, Finding, FindingLocation, RunReport
from shipgate.frontend.domain.models import RunStatus
from shipgate.frontend.domain.requirements import acknowledge
from shipgate.frontend.services.ingest import ingest_run_report
from shipgate.frontend.storage.sqlite import SqliteStorage
from shipgate.frontend.web.app import create_app
from shipgate.paths import PROJECT_SERVER_DIR, SERVER_DB_FILENAME
from shipgate.runtime.report_store import ReportStore

DEFAULT_RUN_ID = "test-run-001"


def sample_failed_report(*, run_id: str = DEFAULT_RUN_ID) -> RunReport:
    return RunReport(
        run_id=run_id,
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
                        location=FindingLocation(path="src/app.py", line=3),
                        extra={
                            "docs_url": "https://docs.astral.sh/ruff/rules/unused-import/",
                            "suggested_commands": ["ruff check --fix"],
                        },
                    ),
                    Finding(
                        check_id="ruff.lint",
                        rule_id="E501",
                        severity="warning",
                        message="line too long",
                        location=FindingLocation(path="src/other.py", line=10),
                    ),
                ),
            ),
            CheckReport(
                check_id="gitleaks.scan",
                tool_id="gitleaks.scan",
                status="failed",
                exit_code=1,
                findings=(),
                stdout_path=f".shipgate/reports/runs/{run_id}/stdout.log",
            ),
            CheckReport(
                check_id="gate.python_gates",
                tool_id="gate.python_gates",
                status="failed",
                exit_code=1,
                findings=(),
            ),
        ),
    )


def sample_baseline_report() -> RunReport:
    """Baseline that shares F401 and adds a finding that current run fixed."""
    return RunReport(
        run_id="baseline",
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
                        location=FindingLocation(path="src/app.py", line=3),
                    ),
                    Finding(
                        check_id="ruff.lint",
                        rule_id="F841",
                        severity="warning",
                        message="unused variable",
                        location=FindingLocation(path="src/old.py", line=2),
                    ),
                ),
            ),
        ),
    )


def prepare_frontend_root(root: Path) -> Path:
    root = Path(root)
    (root / PROJECT_SERVER_DIR).mkdir(parents=True, exist_ok=True)
    acknowledge(root)
    return root


def seed_failed_run(
    root: Path,
    *,
    run_id: str = DEFAULT_RUN_ID,
    with_baseline: bool = False,
    with_report_store: bool = True,
) -> SqliteStorage:
    prepare_frontend_root(root)
    storage = SqliteStorage(root / PROJECT_SERVER_DIR / SERVER_DB_FILENAME)
    run = storage.create_run(branch="main", suite_id="standard", run_id=run_id)
    report = sample_failed_report(run_id=run_id)
    if with_report_store:
        log_path = root / ".shipgate" / "reports" / "runs" / run_id / "stdout.log"
        log_path.parent.mkdir(parents=True, exist_ok=True)
        log_path.write_text("tool stdout\n", encoding="utf-8")
        ReportStore(root).save(report, metadata={"branch": "main"})
    summary = ingest_run_report(storage, run.id, report, root)
    storage.update_run(run.id, status=RunStatus.FAILED, finished=True, summary=summary)
    if with_baseline:
        save_baseline(root, sample_baseline_report())
    return storage


def make_seeded_client(root: Path, *, with_baseline: bool = False) -> TestClient:
    seed_failed_run(root, with_baseline=with_baseline)
    return TestClient(create_app(root))
