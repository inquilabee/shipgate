from pathlib import Path

from shipgate.domain.catalog import ToolDefinition
from shipgate.domain.execution import ExecutionEnvironment, ResolvedRequest
from shipgate.domain.modes import RunMode
from shipgate.domain.options import NormalizedOptions
from shipgate.domain.reports import CheckReport
from shipgate.frontend.services.ingest import is_tool_failure
from shipgate.normalize import get_normalizer
from shipgate.normalize.jscpd import JscpdNormalizer
from shipgate.runtime.executor import ProcessResult


def make_request(
    tmp_path: Path, *, tool_id: str = "jscpd.check.python"
) -> ResolvedRequest:
    config = tmp_path / "jscpd.json"
    config.write_text(
        '{"output": ".shipgate/reports/jscpd-python", "reporters": ["json"]}',
        encoding="utf-8",
    )
    tool = ToolDefinition(id=tool_id, executable="jscpd", normalizer="jscpd")
    return ResolvedRequest(
        runnable=tool_id,
        tool=tool,
        mode=RunMode.CHECK,
        options=NormalizedOptions(paths=(tmp_path,), config=(config,)),
        option_sources={},
        extra_args=(),
        project_root=tmp_path,
        output_path=tmp_path / "out.json",
        environment=ExecutionEnvironment(kind="system", root=None, env={}),
    )


def write_report(
    tmp_path: Path,
    *,
    percentage: float = 2.4,
    with_clone: bool = True,
) -> Path:
    report_dir = tmp_path / ".shipgate" / "reports" / "jscpd-python"
    report_dir.mkdir(parents=True)
    duplicates = []
    if with_clone:
        duplicates.append(
            {
                "format": "python",
                "lines": 8,
                "tokens": 63,
                "firstFile": {
                    "name": "src/app.py",
                    "start": 10,
                    "startLoc": {"line": 10, "column": 1},
                },
                "secondFile": {
                    "name": "src/other.py",
                    "start": 20,
                    "startLoc": {"line": 20, "column": 1},
                },
            }
        )
    payload = {
        "duplicates": duplicates,
        "statistics": {
            "total": {
                "percentage": percentage,
                "clones": len(duplicates),
                "duplicatedLines": 8,
                "lines": 100,
            }
        },
    }
    path = report_dir / "jscpd-report.json"
    path.write_text(__import__("json").dumps(payload), encoding="utf-8")
    return path


def threshold_failure_result(tmp_path: Path) -> ProcessResult:
    return ProcessResult(
        argv=(),
        cwd=tmp_path,
        exit_code=1,
        stdout="",
        stderr=(
            "Using config from jscpd.json\n"
            "ERROR: jscpd found too many duplicates (2.4%) over threshold (2.0%)\n"
        ),
        duration_ms=1,
    )


def assert_threshold_report_shape(report: CheckReport) -> None:
    assert report.status == "failed"
    assert all(finding.rule_id != "TOOL_EXIT" for finding in report.findings)
    assert any(finding.rule_id == "threshold" for finding in report.findings)
    assert any(finding.rule_id == "duplicate" for finding in report.findings)


def assert_clone_finding(report: CheckReport) -> None:
    clone = next(
        finding for finding in report.findings if finding.rule_id == "duplicate"
    )
    assert clone.location is not None
    assert clone.location.path == "src/app.py"
    assert clone.location.line == 10
    threshold = next(f for f in report.findings if f.rule_id == "threshold")
    assert not is_tool_failure(threshold)
    assert not is_tool_failure(clone)


def test_jscpd_threshold_is_code_finding_not_tool_exit(tmp_path: Path):
    write_report(tmp_path)
    report = JscpdNormalizer().normalize(
        make_request(tmp_path),
        threshold_failure_result(tmp_path),
    )
    assert_threshold_report_shape(report)
    assert_clone_finding(report)


def test_jscpd_pass_is_empty(tmp_path: Path):
    report = JscpdNormalizer().normalize(
        make_request(tmp_path),
        ProcessResult(
            argv=(),
            cwd=tmp_path,
            exit_code=0,
            stdout="Found 0 clones.",
            stderr="",
            duration_ms=1,
        ),
    )
    assert report.status == "passed"
    assert report.findings == ()


def test_jscpd_crash_without_threshold_stays_tool_exit(tmp_path: Path):
    report = JscpdNormalizer().normalize(
        make_request(tmp_path),
        ProcessResult(
            argv=(),
            cwd=tmp_path,
            exit_code=1,
            stdout="",
            stderr="Error: Cannot find module 'jscpd'",
            duration_ms=1,
        ),
    )
    assert report.findings[0].rule_id == "TOOL_EXIT"


def test_jscpd_registered():
    assert isinstance(get_normalizer("jscpd"), JscpdNormalizer)
