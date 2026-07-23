import json
from pathlib import Path

from shipgate.catalog.loader import CatalogLoader
from shipgate.domain.execution import ExecutionEnvironment, ResolvedRequest
from shipgate.domain.modes import RunMode
from shipgate.domain.options import NormalizedOptions
from shipgate.normalize.ty import TyNormalizer
from shipgate.runtime.executor import ProcessResult


def test_ty_normalizer_parses_gitlab_json(tmp_path: Path):
    tool = CatalogLoader.load().get_tool("ty.check")
    resolved = ResolvedRequest(
        runnable="ty.check",
        tool=tool,
        mode=RunMode.CHECK,
        options=NormalizedOptions(format="gitlab"),
        option_sources={},
        extra_args=(),
        project_root=tmp_path,
        output_path=tmp_path / ".shipgate/reports/raw/ty.check.json",
        environment=ExecutionEnvironment(kind="system", root=None, env={}),
    )
    payload = [
        {
            "check_name": "invalid-argument-type",
            "description": "invalid-argument-type: bad argument",
            "severity": "major",
            "location": {
                "path": "src/app.py",
                "positions": {"begin": {"line": 12, "column": 4}},
            },
        }
    ]
    result = ProcessResult(
        argv=("ty", "check"),
        cwd=tmp_path,
        exit_code=1,
        stdout=json.dumps(payload),
        stderr="",
        duration_ms=1,
    )
    report = TyNormalizer().normalize(resolved, result)
    assert report.status == "failed"
    assert report.findings[0].rule_id == "invalid-argument-type"
    assert report.findings[0].location is not None
    assert report.findings[0].location.path == "src/app.py"
    assert report.findings[0].location.line == 12
