import json
from pathlib import Path

from shipgate.catalog.loader import load_catalog
from shipgate.domain.execution import ExecutionEnvironment, ResolvedRequest
from shipgate.domain.modes import RunMode
from shipgate.domain.options import NormalizedOptions
from shipgate.normalize.bandit import BanditNormalizer
from shipgate.runtime.executor import ProcessResult


def test_bandit_normalizer_parses_results(tmp_path: Path):
    tool = load_catalog().get_tool("bandit.scan")
    resolved = ResolvedRequest(
        runnable="bandit.scan",
        tool=tool,
        mode=RunMode.CHECK,
        options=NormalizedOptions(),
        option_sources={},
        extra_args=(),
        project_root=tmp_path,
        output_path=tmp_path / ".shipgate/reports/raw/bandit.json",
        environment=ExecutionEnvironment(kind="system", root=None, env={}),
    )
    payload = {
        "results": [
            {
                "filename": "app.py",
                "line_number": 3,
                "test_id": "B101",
                "issue_severity": "HIGH",
                "issue_text": "use of assert",
            }
        ]
    }
    result = ProcessResult(
        argv=("bandit",),
        cwd=tmp_path,
        exit_code=1,
        stdout=json.dumps(payload),
        stderr="",
        duration_ms=1,
    )
    report = BanditNormalizer().normalize(resolved, result)
    assert report.status == "failed"
    assert report.findings[0].rule_id == "B101"
    location = report.findings[0].location
    assert location is not None
    assert location.path == "app.py"


def test_bandit_normalizer_reads_json_from_output_file_with_progress_stdout(tmp_path: Path):
    tool = load_catalog().get_tool("bandit.scan")
    output_path = tmp_path / ".shipgate/reports/raw/bandit.scan.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "results": [
            {
                "filename": "app.py",
                "line_number": 3,
                "test_id": "B101",
                "issue_severity": "HIGH",
                "issue_text": "use of assert",
            }
        ]
    }
    output_path.write_text(json.dumps(payload), encoding="utf-8")
    resolved = ResolvedRequest(
        runnable="bandit.scan",
        tool=tool,
        mode=RunMode.CHECK,
        options=NormalizedOptions(output=output_path, format="json"),
        option_sources={},
        extra_args=(),
        project_root=tmp_path,
        output_path=output_path,
        environment=ExecutionEnvironment(kind="system", root=None, env={}),
    )
    result = ProcessResult(
        argv=("bandit",),
        cwd=tmp_path,
        exit_code=1,
        stdout="Working... ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 100% 0:00:00\n",
        stderr="[json]\tINFO\tJSON output written to file",
        duration_ms=1,
    )
    report = BanditNormalizer().normalize(resolved, result)
    assert report.status == "failed"
    assert report.findings[0].rule_id == "B101"


def test_bandit_normalizer_falls_back_on_unparseable_output(tmp_path: Path):
    tool = load_catalog().get_tool("bandit.scan")
    resolved = ResolvedRequest(
        runnable="bandit.scan",
        tool=tool,
        mode=RunMode.CHECK,
        options=NormalizedOptions(),
        option_sources={},
        extra_args=(),
        project_root=tmp_path,
        output_path=tmp_path / ".shipgate/reports/raw/bandit.scan.json",
        environment=ExecutionEnvironment(kind="system", root=None, env={}),
    )
    result = ProcessResult(
        argv=("bandit",),
        cwd=tmp_path,
        exit_code=2,
        stdout="not json",
        stderr="bandit: command failed",
        duration_ms=1,
    )
    report = BanditNormalizer().normalize(resolved, result)
    assert report.status == "failed"
    assert report.findings[0].rule_id == "TOOL_EXIT"
    assert "bandit: command failed" in report.findings[0].message
