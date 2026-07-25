"""Tests for pyproject.toml [tool.shipgate] config loading."""

from pathlib import Path

import pytest

from shipgate.config.loader import ProjectConfigLoader
from shipgate.errors import ConfigError
from shipgate.paths import PROJECT_CACHE_ENV, SHIPGATE_YAML
from shipgate.project.init import init_project


def assert_config_error(action, *, contains: str) -> None:
    with pytest.raises(ConfigError, match=contains):
        action()


FULL_PYPROJECT = """\
[project]
name = "demo"

[tool.ty.src]
include = ["src", "tests/unit"]
exclude = ["src/generated"]

[tool.shipgate]
suite = "full"
env = "managed"
target = "."
changed_only = true
error_format = "compact"
auto_install = true
parallel = true
fail_fast = true
since = "main"

[tool.shipgate.configs]
mode = "repo"

[tool.shipgate.checks."ruff.lint"]

[tool.shipgate.checks."ruff.format"]

[tool.shipgate.checks."radon.cc"]
threshold = "B"

[tool.shipgate.checks."semgrep.scan"]
scope = "semgrep"

[tool.shipgate.scopes.python-source]
source = "tool.ty.src"

[tool.shipgate.scopes.custom]
include = ["src/foo"]
exclude = ["src/foo/legacy"]
target = "."
respect_gitignore = false
"""


def write_pyproject(tmp_path: Path, content: str = FULL_PYPROJECT) -> Path:
    path = tmp_path / "pyproject.toml"
    path.write_text(content, encoding="utf-8")
    return path


def assert_full_pyproject_top_level(config) -> None:
    assert_full_pyproject_identity(config)
    assert_full_pyproject_runtime_flags(config)


def assert_full_pyproject_identity(config) -> None:
    assert config.suite == "full", "expected full suite"
    assert config.env == "managed", "expected managed env"
    assert config.target == Path(), "expected default target"
    assert config.error_format == "compact", "expected compact error format"
    assert config.config_mode == "repo", "expected repo config mode"
    assert config.checks == (), "expected empty checks tuple"


def assert_full_pyproject_runtime_flags(config) -> None:
    assert config.changed_only is True, "expected changed_only"
    assert config.auto_install is True, "expected auto_install"
    assert config.parallel is True, "expected parallel"
    assert config.fail_fast is True, "expected fail_fast"
    assert config.since == "main", "expected since main"


def assert_full_pyproject_bindings(config) -> None:
    assert len(config.check_bindings) == 4, "expected four check bindings"
    assert {binding.runnable for binding in config.check_bindings} == {
        "ruff.lint",
        "ruff.format",
        "radon.cc",
        "semgrep.scan",
    }, "unexpected runnable set"
    radon = next(binding for binding in config.check_bindings if binding.runnable == "radon.cc")
    assert radon.threshold == "B", "expected radon threshold B"
    semgrep = next(
        binding for binding in config.check_bindings if binding.runnable == "semgrep.scan"
    )
    assert semgrep.scope == "semgrep", "expected semgrep scope"


def assert_full_pyproject_scopes(config) -> None:
    assert config.scopes is not None, "expected scopes"
    python_source = config.scopes["python-source"]
    assert python_source.include == ("src", "tests/unit"), "python-source include"
    assert python_source.exclude == ("src/generated",), "python-source exclude"
    custom = config.scopes["custom"]
    assert custom.include == ("src/foo",), "custom include"
    assert custom.exclude == ("src/foo/legacy",), "custom exclude"
    assert custom.respect_gitignore is False, "custom respect_gitignore"


def assert_yaml_merge_overrides(config) -> None:
    assert_yaml_merge_policy(config)
    assert_yaml_merge_scopes(config)


def assert_yaml_merge_policy(config) -> None:
    assert config.suite == "python-quality", "yaml should override suite"
    assert config.changed_only is False, "yaml should override changed_only"
    assert config.error_format == "compact", "pyproject error_format should remain"
    assert {binding.runnable for binding in config.check_bindings} >= {
        "ty.check",
        "radon.cc",
    }, "merged checks"
    ty = next(binding for binding in config.check_bindings if binding.runnable == "ty.check")
    assert ty.scope == "custom", "ty.check scope"


def assert_yaml_merge_scopes(config) -> None:
    assert config.scopes is not None, "expected scopes"
    assert config.scopes["custom"].include == ("src/bar",), "yaml custom scope"
    assert config.scopes["python-source"].include == (
        "src",
        "tests/unit",
    ), "pyproject scope kept"


def test_pyproject_only_loads_full_config(tmp_path: Path):
    write_pyproject(tmp_path)
    config = ProjectConfigLoader.load(project_root=tmp_path)
    assert_full_pyproject_top_level(config)
    assert_full_pyproject_bindings(config)
    assert_full_pyproject_scopes(config)


def test_pyproject_merges_with_yaml_override(tmp_path: Path):
    write_pyproject(tmp_path)
    (tmp_path / SHIPGATE_YAML).parent.mkdir(parents=True)
    (tmp_path / SHIPGATE_YAML).write_text(
        "suite: python-quality\n"
        "changed-only: false\n"
        "checks:\n"
        "  ty.check:\n"
        "    scope: custom\n"
        "scopes:\n"
        "  custom:\n"
        "    include:\n"
        "      - src/bar\n",
        encoding="utf-8",
    )
    config = ProjectConfigLoader.load(project_root=tmp_path)
    assert_yaml_merge_overrides(config)


def test_explicit_pyproject_config_path(tmp_path: Path):
    write_pyproject(tmp_path)
    (tmp_path / "shipgate.yaml").write_text("suite: format\n", encoding="utf-8")
    config = ProjectConfigLoader.load(
        project_root=tmp_path,
        config_path=tmp_path / "pyproject.toml",
    )
    assert config.suite == "full"


def test_explicit_toml_example_filename(tmp_path: Path):
    example = tmp_path / "pyproject.toml.example"
    example.write_text(FULL_PYPROJECT, encoding="utf-8")
    config = ProjectConfigLoader.load(project_root=tmp_path, config_path=example)
    assert config.suite == "full"


def test_scope_source_from_gate_scan_roots(tmp_path: Path):
    write_pyproject(
        tmp_path,
        """\
[project]
name = "demo"

[tool.shipgate]
suite = "full"

[tool.shipgate.scopes.gate-scope]
source = "gate:gate.module-size"
""",
    )
    gate_dir = tmp_path / ".shipgate" / "configs" / "gates"
    gate_dir.mkdir(parents=True)
    (gate_dir / "gate.module-size.yaml").write_text(
        "scan_roots:\n  - src/\n  - tests/\n",
        encoding="utf-8",
    )
    config = ProjectConfigLoader.load(project_root=tmp_path)
    assert config.scopes is not None
    assert config.scopes["gate-scope"].include == ("src/", "tests/")


def test_scope_source_explicit_paths_override_source_lists(tmp_path: Path):
    write_pyproject(
        tmp_path,
        """\
[project]
name = "demo"

[tool.ty.src]
include = ["src"]

[tool.shipgate.scopes.python-source]
source = "tool.ty.src"
include = ["src/override"]
exclude = ["src/legacy"]
""",
    )
    config = ProjectConfigLoader.load(project_root=tmp_path)
    assert config.scopes is not None
    scope = config.scopes["python-source"]
    assert scope.include == ("src/override",)
    assert scope.exclude == ("src/legacy",)


def test_empty_shipgate_section_returns_defaults(tmp_path: Path):
    write_pyproject(
        tmp_path,
        """\
[project]
name = "demo"

[tool.shipgate]
""",
    )
    config = ProjectConfigLoader.load(project_root=tmp_path)
    assert config.suite == "standard"
    assert config.env == "managed"


def test_unknown_pyproject_key_fails(tmp_path: Path):
    write_pyproject(
        tmp_path,
        """\
[project]
name = "demo"

[tool.shipgate]
unknown = true
""",
    )
    with pytest.raises(ConfigError) as exc_info:
        ProjectConfigLoader.load(project_root=tmp_path)
    assert exc_info.value.exit_code == 2


def test_invalid_pyproject_toml_fails(tmp_path: Path):
    path = tmp_path / "pyproject.toml"
    path.write_text("[tool.shipgate\nsuite = 'full'\n", encoding="utf-8")
    assert_config_error(
        lambda: ProjectConfigLoader.load(project_root=tmp_path),
        contains="invalid TOML",
    )


def test_checks_list_form(tmp_path: Path):
    write_pyproject(
        tmp_path,
        """\
[project]
name = "demo"

[tool.shipgate]
checks = ["ruff.lint", "ruff.format"]
""",
    )
    config = ProjectConfigLoader.load(project_root=tmp_path)
    assert config.checks == ("ruff.lint", "ruff.format")
    assert config.check_bindings == ()


def test_invalid_tool_source_fails(tmp_path: Path):
    write_pyproject(
        tmp_path,
        """\
[project]
name = "demo"

[tool.shipgate.scopes.python-source]
source = "tool.missing.section"
""",
    )
    assert_config_error(
        lambda: ProjectConfigLoader.load(project_root=tmp_path),
        contains="not found",
    )


def test_invalid_gate_source_fails(tmp_path: Path):
    write_pyproject(
        tmp_path,
        """\
[project]
name = "demo"

[tool.shipgate.scopes.gate-scope]
source = "gate:gate.missing"
""",
    )
    assert_config_error(
        lambda: ProjectConfigLoader.load(project_root=tmp_path), contains="gate source not found"
    )


def test_init_writes_pyproject_when_present(tmp_path: Path):
    (tmp_path / "pyproject.toml").write_text("[project]\nname = 'demo'\n", encoding="utf-8")
    path = init_project(tmp_path, mode="pyproject")
    assert path is not None, "init should return pyproject path"
    assert path == tmp_path / "pyproject.toml"
    assert "[tool.shipgate]" in path.read_text(encoding="utf-8")
    assert not (tmp_path / SHIPGATE_YAML).is_file()
    config = ProjectConfigLoader.load(project_root=tmp_path)
    assert config.changed_only is True


def test_init_force_yaml_with_pyproject(tmp_path: Path):
    (tmp_path / "pyproject.toml").write_text("[project]\nname = 'demo'\n", encoding="utf-8")
    path = init_project(tmp_path, mode="yaml")
    assert path == (tmp_path / SHIPGATE_YAML)
    assert "[tool.shipgate]" not in (tmp_path / "pyproject.toml").read_text(encoding="utf-8")


def test_allowlists_parse_from_pyproject(tmp_path: Path):
    write_pyproject(
        tmp_path,
        """\
[project]
name = "demo"

[tool.shipgate]
suite = "full"

[tool.shipgate.allowlists]
"gate.acronym-allowlist" = ".shipgate/allowlists/acronyms.yaml"
"gate.module-size" = ".shipgate/allowlists/module-size.yaml"
""",
    )
    config = ProjectConfigLoader.load(project_root=tmp_path)
    assert config.allowlists == {
        "gate.acronym-allowlist": ".shipgate/allowlists/acronyms.yaml",
        "gate.module-size": ".shipgate/allowlists/module-size.yaml",
    }


def test_allowlists_mapping_value_fails(tmp_path: Path):
    write_pyproject(
        tmp_path,
        """\
[project]
name = "demo"

[tool.shipgate.allowlists."gate.module-size"]
path = ".shipgate/allowlists/module-size.yaml"
reason = "Oversized modules pending split"
""",
    )
    assert_config_error(
        lambda: ProjectConfigLoader.load(project_root=tmp_path),
        contains="must be an allowlist file path",
    )


def test_allowlists_invalid_value_fails(tmp_path: Path):
    write_pyproject(
        tmp_path,
        """\
[project]
name = "demo"

[tool.shipgate.allowlists]
"gate.module-size" = 42
""",
    )
    assert_config_error(
        lambda: ProjectConfigLoader.load(project_root=tmp_path),
        contains="must be an allowlist file path",
    )


def test_yaml_merge_overrides_allowlists(tmp_path: Path):
    write_pyproject(
        tmp_path,
        """\
[project]
name = "demo"

[tool.shipgate.allowlists]
"gate.module-size" = ".shipgate/allowlists/module-size.yaml"
""",
    )
    (tmp_path / SHIPGATE_YAML).parent.mkdir(parents=True)
    (tmp_path / SHIPGATE_YAML).write_text(
        "allowlists:\n  gate.module-size: custom/module-size.yaml\n",
        encoding="utf-8",
    )
    config = ProjectConfigLoader.load(project_root=tmp_path)
    assert config.allowlists == {
        "gate.module-size": "custom/module-size.yaml",
    }


def test_pyproject_example_loads():
    example = Path(__file__).resolve().parents[3] / ".shipgate" / "pyproject.toml.example"
    config = ProjectConfigLoader.load(config_path=example, project_root=example.parent.parent)
    assert config.suite == "full"
    assert config.allowlists is not None
    assert "gate.acronym-allowlist" in config.allowlists


def test_policy_pyproject_prefers_pyproject_when_only_pyproject(tmp_path: Path):
    write_pyproject(tmp_path)
    env_path = tmp_path / PROJECT_CACHE_ENV
    env_path.parent.mkdir(parents=True)
    env_path.write_text(
        f"SHIPGATE_ROOT={tmp_path.resolve()}\nSHIPGATE_POLICY=pyproject\n",
        encoding="utf-8",
    )
    config = ProjectConfigLoader.load(project_root=tmp_path)
    assert config.suite == "full"


def test_policy_yaml_prefers_yaml_when_both_exist(tmp_path: Path):
    write_pyproject(tmp_path)
    (tmp_path / SHIPGATE_YAML).parent.mkdir(parents=True)
    (tmp_path / SHIPGATE_YAML).write_text("suite: python-quality\n", encoding="utf-8")
    env_path = tmp_path / PROJECT_CACHE_ENV
    env_path.parent.mkdir(parents=True)
    env_path.write_text(
        f"SHIPGATE_ROOT={tmp_path.resolve()}\nSHIPGATE_POLICY=yaml\n",
        encoding="utf-8",
    )
    config = ProjectConfigLoader.load(project_root=tmp_path)
    assert config.suite == "python-quality"
