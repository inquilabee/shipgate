from shipgate.domain.reports import (
    SCHEMA_VERSION,
    CheckReport,
    Finding,
    FindingLocation,
    RunReport,
)
from shipgate.domain.run_command import RunCommand
from shipgate.runtime.report_store import ReportStore
from shipgate.runtime.reports import generate_run_id
from shipgate.runtime.session.finalizer import finalize_failed_run


def test_finalize_failed_run_sets_report_path_and_indexes(tmp_path):
    report = RunReport(
        run_id="20260101T000000Z-abc123",
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
    command = RunCommand(project_root=tmp_path, quiet=True)
    exit_code, finalized = finalize_failed_run(
        command,
        tmp_path,
        report,
        "compact",
        write_reports=True,
        emit_failure_output=False,
    )
    assert exit_code == 1
    assert finalized.report_path is not None
    failure_path = tmp_path / finalized.report_path
    assert failure_path.is_file()

    store = ReportStore(tmp_path)
    indexed = store.list_runs()
    assert indexed
    assert indexed[0]["run_id"] == report.run_id
    assert indexed[0]["status"] == "failed"
    assert indexed[0]["finding_count"] == 1
    loaded = store.load(report.run_id)
    assert loaded.status == "failed"
    assert loaded.report_path == finalized.report_path


def test_report_store_rejects_traversal_run_id(tmp_path):
    import pytest

    from shipgate.errors import ExecutionError

    store = ReportStore(tmp_path)
    with pytest.raises(ExecutionError, match="invalid run id"):
        store.load("../secret")


def test_validate_run_id_accepts_generated_ids():
    from shipgate.runtime.reports import validate_run_id

    assert validate_run_id(generate_run_id())


def test_schema_version_in_output():
    report = RunReport(run_id="test", suite="standard", mode="check", status="passed")
    assert report.to_dict()["schema_version"] == SCHEMA_VERSION


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
