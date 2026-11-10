import os

import pytest

from shipgate.domain.reports import (
    SCHEMA_VERSION,
    CheckReport,
    Finding,
    FindingLocation,
    RunReport,
)
from shipgate.domain.run_command import RunCommand
from shipgate.errors import ExecutionError
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


def seed_run(root, run_id: str, age_rank: int) -> None:
    """A stored run in runs/, raw/ and failures/, ``age_rank`` seconds after the epoch."""
    store = ReportStore(root)
    store.save(RunReport(run_id=run_id, suite="standard", mode="check", status="passed"))
    (store.root / "raw" / run_id / "ruff.lint").mkdir(parents=True)
    (store.root / "failures" / run_id).mkdir(parents=True)
    for base in store.run_roots():
        os.utime(base / run_id, (age_rank, age_rank))


RUN_IDS = [f"20260101T00000{n}Z-aaaaaa" for n in range(5)]


@pytest.fixture
def pruned_store(tmp_path):
    for rank, run_id in enumerate(RUN_IDS, start=1):
        seed_run(tmp_path, run_id, rank)
    store = ReportStore(tmp_path)
    (store.root / "raw" / "ruff.lint.json").write_text("{}", encoding="utf-8")
    (store.root / "raw" / "not a run id").mkdir()
    assert store.prune(keep=2) == 3
    return store


def stored_in(store, run_id) -> list[bool]:
    return [(base / run_id).exists() for base in store.run_roots()]


def test_prune_drops_old_runs_from_every_directory_and_the_index(pruned_store):
    assert [stored_in(pruned_store, run_id) for run_id in RUN_IDS] == [
        [False, False, False],
        [False, False, False],
        [False, False, False],
        [True, True, True],
        [True, True, True],
    ]
    assert {entry["run_id"] for entry in pruned_store.list_runs()} == set(RUN_IDS[3:])


def test_prune_leaves_files_and_dirs_that_are_not_run_ids_alone(pruned_store):
    assert (pruned_store.root / "raw" / "ruff.lint.json").is_file()
    assert (pruned_store.root / "raw" / "not a run id").is_dir()


def test_prune_is_a_noop_under_the_limit_and_rejects_a_zero_keep(tmp_path):
    seed_run(tmp_path, "20260101T000000Z-aaaaaa", 1)
    store = ReportStore(tmp_path)
    assert store.prune(keep=5) == 0
    assert len(store.list_runs()) == 1
    with pytest.raises(ExecutionError):
        store.prune(keep=0)
