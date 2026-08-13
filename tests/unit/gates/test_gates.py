import json
from dataclasses import replace
from pathlib import Path

import pytest

from shipgate.catalog.loader import CatalogLoader
from shipgate.domain.catalog import ToolDefinition
from shipgate.domain.execution import ExecutionEnvironment, ResolvedRequest
from shipgate.domain.modes import RunMode
from shipgate.domain.options import NormalizedOptions
from shipgate.domain.reports import CheckReport
from shipgate.gates.paths import gates_lib_path
from shipgate.gates.runtime import (
    gate_scope_paths,
    is_gate_tool,
    prepare_gate_execution,
)
from shipgate.normalize.core import GateJsonNormalizer
from shipgate.runtime.executor import Executor, ProcessResult
from shipgate.runtime.session.check_runner import OutputFileSnapshot


def gate_request(
    tmp_path: Path,
    tool_id: str,
    *,
    paths: tuple[Path, ...],
) -> ResolvedRequest:
    tool = CatalogLoader.load().get_tool(tool_id)
    return ResolvedRequest(
        runnable=tool.id,
        tool=tool,
        mode=RunMode.CHECK,
        options=NormalizedOptions(paths=paths),
        option_sources={},
        extra_args=(),
        project_root=tmp_path,
        output_path=tmp_path / ".shipgate" / "reports" / "raw" / f"{tool.id}.json",
        environment=ExecutionEnvironment(kind="system", root=None, env={}),
    )


def run_gate_check(tmp_path: Path, request: ResolvedRequest) -> tuple[ProcessResult, CheckReport]:
    argv, env = prepare_gate_execution(request)
    snapshot = OutputFileSnapshot.capture(request.output_path)
    result = replace(
        Executor().run(argv, cwd=tmp_path, env=env),
        output_files=snapshot.written_paths(),
    )
    report = GateJsonNormalizer().normalize(request, result)
    return result, report


def test_catalog_includes_bundled_policy_gates():
    catalog = CatalogLoader.load()
    for gate_id in (
        "gate.module-size",
        "gate.module-private-vars",
        "gate.folder-breadth",
        "gate.acronym-allowlist",
        "gate.test-only-symbols",
        "gate.repeated-strings",
        "gate.class-local-functions",
    ):
        tool = catalog.get_tool(gate_id)
        assert tool.normalizer == "gate_json"
        assert tool.module is not None
        assert tool.script is None
        assert is_gate_tool(tool)
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
    output_files: tuple[Path, ...] = (),
) -> ProcessResult:
    return ProcessResult(
        argv=(),
        cwd=tmp_path,
        exit_code=exit_code,
        stdout=stdout,
        stderr=stderr,
        duration_ms=1,
        output_files=output_files,
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


def test_gate_json_normalizer_invalid_json_fails_even_on_exit_zero(tmp_path: Path):
    gate_request = make_gate_request("gate.module-size", tmp_path / "report.json")
    result = process_result(tmp_path, exit_code=0, stdout="{not-json")
    report = GateJsonNormalizer().normalize(gate_request, result)
    assert report.status == "failed"
    assert report.findings[0].rule_id == "gate.invalid_json"


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
    result = process_result(
        tmp_path,
        exit_code=1,
        stdout="",
        stderr="gate failed",
        output_files=(report_path,),
    )
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
    tool = CatalogLoader.load().get_tool("gate.module-size")
    assert is_gate_tool(tool)
    assert tool.module == "shipgate.policy.module_size"
    argv, env = prepare_gate_execution(gate_request(tmp_path, tool.id, paths=(tmp_path / "src",)))
    assert_module_gate_argv(argv, env, tmp_path)
    assert_module_gate_env(env, tmp_path)


def assert_module_gate_argv(argv: tuple[str, ...], env: dict[str, str], root: Path) -> None:
    assert argv[0] == env["SHIPGATE_PYTHON"] or argv[0].endswith("python")
    assert argv[1:3] == ("-m", "shipgate.policy.module_size")
    assert "--root" in argv
    assert str(root) in argv
    assert "--config" in argv
    assert "--report" in argv


def assert_module_gate_env(env: dict[str, str], root: Path) -> None:
    assert env["SHIPGATE_ROOT"] == str(root)
    assert env["SHIPGATE_REPORT"].endswith("gate.module-size.json")
    assert Path(env["SHIPGATE_GATE_CONFIG"]).is_file()
    assert "SHIPGATE_GATES_LIB" not in env
    assert "." in env["GATE_SCAN_ROOTS"]


def test_gate_scope_paths_includes_dirs_for_dir_delivery(tmp_path: Path):
    (tmp_path / "src").mkdir()
    catalog = CatalogLoader.load()
    tool = catalog.get_tool("gate.folder-breadth")
    request = gate_request(tmp_path, tool.id, paths=(Path("src"),))
    assert gate_scope_paths(request) == ("src",)


def test_prepare_gate_execution_sets_scope_paths_for_dirs_delivery(
    tmp_path: Path,
    monkeypatch,
):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "src").mkdir()
    catalog = CatalogLoader.load()
    tool = catalog.get_tool("gate.folder-breadth")
    request = gate_request(tmp_path, tool.id, paths=(Path("src"),))
    _argv, env = prepare_gate_execution(request)
    assert env["SHIPGATE_SCOPE_PATHS"] == "src"


@pytest.mark.integration
def test_module_private_vars_flags_existing_module_function(tmp_path: Path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "tests").mkdir()
    (tmp_path / "tests" / "legacy.py").write_text(
        "def _helper():\n    return 1\n",
        encoding="utf-8",
    )
    tool = CatalogLoader.load().get_tool("gate.module-private-vars")
    request = gate_request(tmp_path, tool.id, paths=(tmp_path / "tests",))
    result, report = run_gate_check(tmp_path, request)
    assert result.exit_code == 1, result.stderr
    assert report.status == "failed"
    assert any(f.rule_id == "private-function" for f in report.findings)


@pytest.mark.integration
def test_module_size_flags_existing_oversized_module(tmp_path: Path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "src").mkdir()
    body = "\n".join("x = 1" for _ in range(501))
    (tmp_path / "src" / "legacy.py").write_text(body + "\n", encoding="utf-8")
    tool = CatalogLoader.load().get_tool("gate.module-size")
    request = gate_request(tmp_path, tool.id, paths=(tmp_path / "src",))
    result, report = run_gate_check(tmp_path, request)
    assert result.exit_code == 1, result.stderr
    assert report.status == "failed"
    assert any(f.rule_id == "module-size" for f in report.findings)


@pytest.mark.integration
def test_bundled_module_size_gate_passes_clean_repo(tmp_path: Path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "small.py").write_text("x = 1\n", encoding="utf-8")
    request = gate_request(
        tmp_path,
        "gate.module-size",
        paths=(tmp_path / "src",),
    )
    result, report = run_gate_check(tmp_path, request)
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
