import json

from shipgate.domain.catalog import ToolDefinition
from shipgate.domain.execution import ExecutionEnvironment, ResolvedRequest
from shipgate.domain.modes import RunMode
from shipgate.domain.options import NormalizedOptions
from shipgate.normalize.ruff import RuffNormalizer
from shipgate.runtime.executor import ProcessResult


def test_empty_list_passed(tmp_path):
    tool = ToolDefinition(id="ruff.lint", executable="ruff", modes=(RunMode.CHECK,))
    request = ResolvedRequest(
        runnable="ruff.lint",
        tool=tool,
        mode=RunMode.CHECK,
        options=NormalizedOptions(),
        option_sources={},
        extra_args=(),
        project_root=tmp_path,
        output_path=tmp_path / "out.json",
        environment=ExecutionEnvironment(kind="system", root=None, env={}),
    )
    result = ProcessResult(
        argv=(),
        cwd=tmp_path,
        exit_code=0,
        stdout="[]",
        stderr="",
        duration_ms=1,
    )
    report = RuffNormalizer().normalize(request, result)
    assert report.status == "passed"


def test_one_finding_maps(tmp_path):
    tool = ToolDefinition(id="ruff.lint", executable="ruff", modes=(RunMode.CHECK,))
    request = ResolvedRequest(
        runnable="ruff.lint",
        tool=tool,
        mode=RunMode.CHECK,
        options=NormalizedOptions(),
        option_sources={},
        extra_args=(),
        project_root=tmp_path,
        output_path=tmp_path / "out.json",
        environment=ExecutionEnvironment(kind="system", root=None, env={}),
    )
    payload = [
        {
            "code": "F401",
            "message": "Unused import",
            "filename": "src/main.py",
            "location": {"row": 12, "column": 5},
        }
    ]
    result = ProcessResult(
        argv=(),
        cwd=tmp_path,
        exit_code=1,
        stdout=json.dumps(payload),
        stderr="",
        duration_ms=1,
    )
    report = RuffNormalizer().normalize(request, result)
    assert len(report.findings) == 1
    f = report.findings[0]
    assert f.rule_id == "F401"
    assert f.location is not None
    assert f.location.line == 12
