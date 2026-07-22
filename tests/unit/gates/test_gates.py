import json
from pathlib import Path

import pytest

from shipgate.catalog.loader import load_catalog
from shipgate.domain.catalog import ToolDefinition
from shipgate.domain.execution import ExecutionEnvironment, ResolvedRequest
from shipgate.domain.modes import RunMode
from shipgate.domain.options import NormalizedOptions
from shipgate.gates.paths import gates_lib_path, resolve_gate_script
from shipgate.gates.runtime import is_gate_tool, prepare_gate_execution
from shipgate.normalize.gate_json import GateJsonNormalizer
from shipgate.runtime.executor import ProcessResult


def test_catalog_includes_bundled_policy_gates():
    catalog = load_catalog()
    for gate_id in (
        "gate.module-size",
        "gate.module-private-vars",
        "gate.folder-breadth",
        "gate.acronym-allowlist",
    ):
        tool = catalog.get_tool(gate_id)
        assert tool.normalizer == "gate_json"
        assert "Gates" in tool.capabilities
        assert tool.script is not None
    assert "policy" in catalog.suites
    assert "gate.module-size" in catalog.suites["policy"].members
    assert "policy" in catalog.suites["full"].members
    assert "policy" in catalog.suites["ci"].members


def process_result(
    tmp_path: Path,
    *,
    exit_code: int,
    stdout: str,
    stderr: str = "",
) -> ProcessResult:
    return ProcessResult(
        argv=(),
        cwd=tmp_path,
        exit_code=exit_code,
        stdout=stdout,
        stderr=stderr,
        duration_ms=1,
    )


def test_gate_json_normalizer_parses_findings(tmp_path: Path):
    payload = {
        "findings": [
            {
                "rule_id": "line-limit",
                "severity": "error",
                "message": "too long",
                "location": {"file": "src/a.py", "line": 1},
            }
        ]
    }
    gate_request = make_gate_request("gate.module-size", tmp_path / "report.json")
    result = process_result(tmp_path, exit_code=1, stdout=json.dumps(payload))
    report = GateJsonNormalizer().normalize(gate_request, result)
    assert report.status == "failed"
    assert len(report.findings) == 1
    assert report.findings[0].rule_id == "line-limit"
    assert report.findings[0].location is not None
    assert report.findings[0].location.path == "src/a.py"
    assert report.findings[0].location.line == 1


def test_gate_json_normalizer_reads_output_file(tmp_path: Path):
    report_path = tmp_path / "gate.json"
    report_path.write_text(
        json.dumps(
            {
                "findings": [
                    {
                        "rule_id": "folder-breadth",
                        "severity": "error",
                        "message": "too many files",
                        "location": {"file": "src/big"},
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    gate_request = make_gate_request("gate.folder-breadth", report_path)
    result = process_result(tmp_path, exit_code=1, stdout="", stderr="gate failed")
    report = GateJsonNormalizer().normalize(gate_request, result)
    assert report.status == "failed"
    assert report.findings[0].message == "too many files"


def test_gates_lib_path_exists():
    path = gates_lib_path()
    assert path.is_file()
    assert path.name == "lib.sh"


def test_prepare_gate_execution_sets_env(tmp_path: Path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "ok.py").write_text("print('ok')\n", encoding="utf-8")
    catalog = load_catalog()
    tool = catalog.get_tool("gate.module-size")
    assert is_gate_tool(tool)
    script = resolve_gate_script(tool, tmp_path)
    assert script.is_file()
    request = ResolvedRequest(
        runnable=tool.id,
        tool=tool,
        mode=RunMode.CHECK,
        options=NormalizedOptions(paths=(tmp_path / "src",)),
        option_sources={},
        extra_args=(),
        project_root=tmp_path,
        output_path=tmp_path / ".shipgate" / "reports" / "raw" / f"{tool.id}.json",
        environment=ExecutionEnvironment(kind="system", root=None, env={}),
    )
    argv, env = prepare_gate_execution(request)
    assert argv[0].endswith("bash")
    assert str(script) in argv[1]
    assert env["SHIPGATE_ROOT"] == str(tmp_path)
    assert env["SHIPGATE_REPORT"].endswith("gate.module-size.json")
    assert Path(env["SHIPGATE_GATE_CONFIG"]).is_file()
    assert env["SHIPGATE_GATES_LIB"].endswith("lib.sh")
    assert "." in env["GATE_SCAN_ROOTS"]


@pytest.mark.integration
def test_module_private_vars_flags_existing_module_function(tmp_path: Path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "tests").mkdir()
    (tmp_path / "tests" / "legacy.py").write_text(
        "def _helper():\n    return 1\n",
        encoding="utf-8",
    )
    catalog = load_catalog()
    tool = catalog.get_tool("gate.module-private-vars")
    request = ResolvedRequest(
        runnable=tool.id,
        tool=tool,
        mode=RunMode.CHECK,
        options=NormalizedOptions(paths=(tmp_path / "tests",)),
        option_sources={},
        extra_args=(),
        project_root=tmp_path,
        output_path=tmp_path / ".shipgate" / "reports" / "raw" / f"{tool.id}.json",
        environment=ExecutionEnvironment(kind="system", root=None, env={}),
    )
    argv, env = prepare_gate_execution(request)
    from shipgate.runtime.executor import Executor

    result = Executor().run(argv, cwd=tmp_path, env=env)
    report = GateJsonNormalizer().normalize(request, result)
    assert result.exit_code == 1, result.stderr
    assert report.status == "failed"
    assert any(f.rule_id == "private-function" for f in report.findings)


@pytest.mark.integration
def test_module_size_flags_existing_oversized_module(tmp_path: Path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "src").mkdir()
    body = "\n".join("x = 1" for _ in range(501))
    (tmp_path / "src" / "legacy.py").write_text(body + "\n", encoding="utf-8")
    catalog = load_catalog()
    tool = catalog.get_tool("gate.module-size")
    request = ResolvedRequest(
        runnable=tool.id,
        tool=tool,
        mode=RunMode.CHECK,
        options=NormalizedOptions(paths=(tmp_path / "src",)),
        option_sources={},
        extra_args=(),
        project_root=tmp_path,
        output_path=tmp_path / ".shipgate" / "reports" / "raw" / f"{tool.id}.json",
        environment=ExecutionEnvironment(kind="system", root=None, env={}),
    )
    argv, env = prepare_gate_execution(request)
    from shipgate.runtime.executor import Executor

    result = Executor().run(argv, cwd=tmp_path, env=env)
    report = GateJsonNormalizer().normalize(request, result)
    assert result.exit_code == 1, result.stderr
    assert report.status == "failed"
    assert any(f.rule_id == "module-size" for f in report.findings)


@pytest.mark.integration
def test_bundled_module_size_gate_passes_clean_repo(tmp_path: Path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "small.py").write_text("x = 1\n", encoding="utf-8")
    catalog = load_catalog()
    tool = catalog.get_tool("gate.module-size")
    request = ResolvedRequest(
        runnable=tool.id,
        tool=tool,
        mode=RunMode.CHECK,
        options=NormalizedOptions(paths=(tmp_path / "src",)),
        option_sources={},
        extra_args=(),
        project_root=tmp_path,
        output_path=tmp_path / ".shipgate" / "reports" / "raw" / f"{tool.id}.json",
        environment=ExecutionEnvironment(kind="system", root=None, env={}),
    )
    argv, env = prepare_gate_execution(request)
    from shipgate.runtime.executor import Executor

    result = Executor().run(argv, cwd=tmp_path, env=env)
    report = GateJsonNormalizer().normalize(request, result)
    assert result.exit_code == 0, result.stderr
    assert report.status == "passed"


def make_gate_request(tool_id: str, output_path: Path) -> ResolvedRequest:
    tool = ToolDefinition(id=tool_id, executable="bash", modes=(RunMode.CHECK,))
    return ResolvedRequest(
        runnable=tool_id,
        tool=tool,
        mode=RunMode.CHECK,
        options=NormalizedOptions(output=output_path),
        option_sources={},
        extra_args=(),
        project_root=Path(),
        output_path=output_path,
        environment=ExecutionEnvironment(kind="system", root=None, env={}),
    )
