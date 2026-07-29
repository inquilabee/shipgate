"""Shared fixtures and assertions for pyproject config loader tests."""

from __future__ import annotations

from pathlib import Path

import pytest

from shipgate.errors import ConfigError

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


def assert_config_error(action, *, contains: str) -> None:
    with pytest.raises(ConfigError, match=contains):
        action()


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
