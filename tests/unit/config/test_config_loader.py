from pathlib import Path

import pytest

from shipgate.config.loader import load_config
from shipgate.errors import ConfigError


def test_missing_config_returns_defaults(tmp_path):
    config = load_config(project_root=tmp_path)
    assert config.suite == "standard"
    assert config.env == "managed"
    assert config.target == Path(".")


def test_minimal_config_parses(tmp_path):
    (tmp_path / "shipgate.yaml").write_text("suite: python-quality\n")
    config = load_config(project_root=tmp_path)
    assert config.suite == "python-quality"


def test_unknown_key_fails(tmp_path):
    (tmp_path / "shipgate.yaml").write_text("unknown: true\n")
    with pytest.raises(ConfigError) as exc:
        load_config(project_root=tmp_path)
    assert exc.value.exit_code == 2


def test_invalid_env_fails(tmp_path):
    (tmp_path / "shipgate.yaml").write_text("env: docker\n")
    with pytest.raises(ConfigError):
        load_config(project_root=tmp_path)


def test_invalid_error_format_fails(tmp_path):
    (tmp_path / "shipgate.yaml").write_text("error-format: xml\n")
    with pytest.raises(ConfigError):
        load_config(project_root=tmp_path)


def test_cli_config_wins(tmp_path):
    project = tmp_path / "project"
    project.mkdir()
    (project / "shipgate.yaml").write_text("suite: format\n")
    override = tmp_path / "override.yaml"
    override.write_text("suite: python-quality\n")
    config = load_config(config_path=override, project_root=project)
    assert config.suite == "python-quality"
