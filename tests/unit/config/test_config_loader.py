from pathlib import Path

import pytest

from shipgate.config.loader import ProjectConfigLoader
from shipgate.errors import ConfigError


def test_missing_config_returns_defaults(tmp_path):
    config = ProjectConfigLoader.load(project_root=tmp_path)
    assert config.suite == "standard"
    assert config.env == "managed"
    assert config.target == Path()
    assert config.error_format is None


def test_minimal_config_parses(tmp_path):
    (tmp_path / "shipgate.yaml").write_text("suite: python-quality\n")
    config = ProjectConfigLoader.load(project_root=tmp_path)
    assert config.suite == "python-quality"


def test_unknown_key_fails(tmp_path):
    (tmp_path / "shipgate.yaml").write_text("unknown: true\n")
    with pytest.raises(ConfigError) as exc:
        ProjectConfigLoader.load(project_root=tmp_path)
    assert exc.value.exit_code == 2


def test_invalid_env_fails(tmp_path):
    (tmp_path / "shipgate.yaml").write_text("env: docker\n")
    with pytest.raises(ConfigError):
        ProjectConfigLoader.load(project_root=tmp_path)


def test_invalid_error_format_fails(tmp_path):
    (tmp_path / "shipgate.yaml").write_text("error-format: xml\n")
    with pytest.raises(ConfigError):
        ProjectConfigLoader.load(project_root=tmp_path)


def test_cli_config_wins(tmp_path):
    project = tmp_path / "project"
    project.mkdir()
    (project / "shipgate.yaml").write_text("suite: format\n")
    override = tmp_path / "override.yaml"
    override.write_text("suite: python-quality\n")
    config = ProjectConfigLoader.load(config_path=override, project_root=project)
    assert config.suite == "python-quality"


def test_check_bindings_parse_scope_and_threshold(tmp_path):
    (tmp_path / "shipgate.yaml").write_text(
        "suite: full\nchecks:\n  radon.cc:\n    threshold: B\n  semgrep.scan:\n    scope: semgrep\n"
    )
    config = ProjectConfigLoader.load(project_root=tmp_path)
    assert config.checks == ()
    assert len(config.check_bindings) == 2
    radon = next(b for b in config.check_bindings if b.runnable == "radon.cc")
    assert radon.threshold == "B"
    semgrep = next(b for b in config.check_bindings if b.runnable == "semgrep.scan")
    assert semgrep.scope == "semgrep"


def test_incremental_config_parses(tmp_path):
    (tmp_path / "shipgate.yaml").write_text(
        "suite: full\nchanged-only: true\nsince: main\n",
    )
    config = ProjectConfigLoader.load(project_root=tmp_path)
    assert config.changed_only is True
    assert config.since == "main"
