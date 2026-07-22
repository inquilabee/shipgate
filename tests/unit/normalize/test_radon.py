from pathlib import Path

from shipgate.domain.catalog import ToolDefinition
from shipgate.domain.execution import ExecutionEnvironment, ResolvedRequest
from shipgate.domain.modes import RunMode
from shipgate.domain.options import NormalizedOptions
from shipgate.normalize.radon import RadonNormalizer
from shipgate.runtime.executor import ProcessResult


def resolved(
    tmp_path: Path,
    tool_id: str,
    subcommand: tuple[str, ...],
    *,
    threshold: str | None = None,
) -> ResolvedRequest:
    tool = ToolDefinition(
        id=tool_id,
        executable="radon",
        subcommand=subcommand,
        normalizer="radon",
    )
    return ResolvedRequest(
        runnable=tool_id,
        tool=tool,
        mode=RunMode.CHECK,
        options=NormalizedOptions(paths=(tmp_path,), threshold=threshold),
        option_sources={},
        extra_args=(),
        project_root=tmp_path,
        output_path=tmp_path / "out.json",
        environment=ExecutionEnvironment(kind="system", root=None, env={}),
    )


def test_radon_cc_allows_rank_a(tmp_path: Path):
    payload = '{"src/app.py": [{"type": "function", "name": "ok", "rank": "A", "lineno": 1}]}'
    report = RadonNormalizer().normalize(
        resolved(tmp_path, "radon.cc", ("cc", "-j")),
        ProcessResult(
            argv=(),
            cwd=tmp_path,
            exit_code=0,
            stdout=payload,
            stderr="",
            duration_ms=1,
        ),
    )
    assert report.status == "passed"
    assert report.findings == ()


def test_radon_cc_allows_rank_b(tmp_path: Path):
    payload = '{"src/app.py": [{"type": "function", "name": "ok", "rank": "B", "lineno": 10}]}'
    report = RadonNormalizer().normalize(
        resolved(tmp_path, "radon.cc", ("cc", "-j")),
        ProcessResult(
            argv=(),
            cwd=tmp_path,
            exit_code=0,
            stdout=payload,
            stderr="",
            duration_ms=1,
        ),
    )
    assert report.status == "passed"
    assert report.findings == ()


def test_radon_cc_allows_rank_c(tmp_path: Path):
    payload = '{"src/app.py": [{"type": "function", "name": "ok", "rank": "C", "lineno": 10}]}'
    report = RadonNormalizer().normalize(
        resolved(tmp_path, "radon.cc", ("cc", "-j")),
        ProcessResult(
            argv=(),
            cwd=tmp_path,
            exit_code=0,
            stdout=payload,
            stderr="",
            duration_ms=1,
        ),
    )
    assert report.status == "passed"
    assert report.findings == ()


def test_radon_cc_fails_rank_c_with_threshold_b(tmp_path: Path):
    payload = '{"src/app.py": [{"type": "function", "name": "ok", "rank": "C", "lineno": 10}]}'
    report = RadonNormalizer().normalize(
        resolved(tmp_path, "radon.cc", ("cc", "-j"), threshold="B"),
        ProcessResult(
            argv=(),
            cwd=tmp_path,
            exit_code=0,
            stdout=payload,
            stderr="",
            duration_ms=1,
        ),
    )
    assert report.status == "failed"
    assert report.findings[0].rule_id == "complexity"


def test_radon_cc_fails_rank_d(tmp_path: Path):
    payload = '{"src/app.py": [{"type": "function", "name": "bad", "rank": "D", "lineno": 10}]}'
    report = RadonNormalizer().normalize(
        resolved(tmp_path, "radon.cc", ("cc", "-j")),
        ProcessResult(
            argv=(),
            cwd=tmp_path,
            exit_code=0,
            stdout=payload,
            stderr="",
            duration_ms=1,
        ),
    )
    assert report.status == "failed"
    assert len(report.findings) == 1
    assert report.findings[0].rule_id == "complexity"
    assert "rank D" in report.findings[0].message


def test_radon_mi_fails_rank_below_c(tmp_path: Path):
    payload = '{"src/app.py": {"rank": "D", "mi": 12.5}}'
    report = RadonNormalizer().normalize(
        resolved(tmp_path, "radon.mi", ("mi", "-j")),
        ProcessResult(
            argv=(),
            cwd=tmp_path,
            exit_code=0,
            stdout=payload,
            stderr="",
            duration_ms=1,
        ),
    )
    assert report.status == "failed"
    assert report.findings[0].rule_id == "maintainability"
