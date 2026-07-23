from shipgate.config.core import ProjectConfigParser
from shipgate.domain.project import ProjectConfig


def test_parse_minimal_config(tmp_path):
    config = ProjectConfigParser.parse(
        {"suite": "python-quality", "env": "managed"},
        tmp_path / "shipgate.yaml",
    )
    assert isinstance(config, ProjectConfig)
    assert config.suite == "python-quality"
    assert config.env == "managed"
