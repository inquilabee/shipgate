import json
import shutil
from pathlib import Path

import pytest

from shipgate.catalog.loader import CatalogLoader
from shipgate.core import run_command
from shipgate.domain.project import ProjectConfig
from shipgate.project.doctor import DoctorReport, ProjectDoctor

GIT = shutil.which("git")


@pytest.fixture
def project(tmp_path: Path) -> Path:
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "a.py").write_text("x = 1\n", encoding="utf-8")
    (tmp_path / "build_out").mkdir()
    (tmp_path / ".gitignore").write_text("build_out/\n", encoding="utf-8")
    shipgate = tmp_path / ".shipgate"
    shipgate.mkdir()
    (shipgate / "shipgate.yaml").write_text("suite: standard\n", encoding="utf-8")
    lock = {"schema_version": "shipgate.lock.v1", "packages": {"ruff": "0.0.1"}}
    (shipgate / "lock.json").write_text(json.dumps(lock), encoding="utf-8")
    assert GIT is not None
    run_command([GIT, "init", "-q"], cwd=tmp_path, check=True)
    return tmp_path


@pytest.fixture
def report(project: Path) -> DoctorReport:
    catalog = CatalogLoader.load()
    ruff = catalog.get_tool("ruff.lint")
    assert ruff.install is not None
    ruff_pin = str(ruff.install.version)
    return ProjectDoctor(
        project,
        ProjectConfig(),
        catalog,
        installed_version=lambda tool: ruff_pin if tool is ruff else None,
    ).report()


@pytest.mark.skipif(GIT is None, reason="git not on PATH")
def test_doctor_explains_what_is_in_and_out_of_scope(report: DoctorReport):
    scope = dict(report.scope)
    assert report.suite_id == "standard"
    assert scope["src"] is None
    assert "gitignore" in (scope["build_out"] or "")
    assert "build_out" in report.render()


@pytest.mark.skipif(GIT is None, reason="git not on PATH")
def test_doctor_flags_policy_files_that_are_not_committed(report: DoctorReport):
    assert dict(report.policy_files)[".shipgate/shipgate.yaml"].startswith("untracked")


@pytest.mark.skipif(GIT is None, reason="git not on PATH")
def test_doctor_compares_installed_versions_with_the_lock(report: DoctorReport):
    states = {state.tool_id: state for state in report.tools}
    assert (states["ruff.lint"].locked, states["ruff.lint"].status) == ("0.0.1", "differs")
    assert states["ty.check"].status == "not installed"
