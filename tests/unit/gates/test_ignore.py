import sys
from pathlib import Path

import pytest

from shipgate.core import run_command
from shipgate.gates.ignore import (
    EffectiveIgnores,
    ignore_env,
    ignores_from_env,
    main,
    patterns_from_env,
)


def test_effective_ignores_matches_gitignore_patterns():
    ignores = EffectiveIgnores(path_patterns=("build/", "*.pyc"))
    assert ignores.is_ignored("build/output.txt")
    assert ignores.is_ignored("src/module.pyc")
    assert not ignores.is_ignored("src/module.py")


def test_effective_ignores_matches_directory_gitignore_prefix():
    ignores = EffectiveIgnores(path_patterns=("notes/", ".cursor/"))
    assert ignores.is_ignored("notes")
    assert ignores.is_ignored("notes/")
    assert ignores.is_ignored("notes/foo.md")
    assert ignores.is_ignored(".cursor")
    assert ignores.is_ignored(".cursor/skills/x.py")
    assert not ignores.is_ignored("src/module.py")


def test_patterns_from_env_reads_paths_and_profiles(monkeypatch, tmp_path):
    profile = tmp_path / "ignore.txt"
    profile.write_text(
        "\n".join(
            [
                "# comment",
                "!negation",
                "vendor/",
            ]
        ),
        encoding="utf-8",
    )
    monkeypatch.setenv("SHIPGATE_IGNORE_PATHS", "dist/\n")
    monkeypatch.setenv("SHIPGATE_IGNORE_PROFILES", f"{profile}\n/missing")

    assert patterns_from_env() == ("dist/", "vendor/")


def test_ignores_from_env(monkeypatch):
    monkeypatch.setenv("SHIPGATE_IGNORE_PATHS", "node_modules/")
    ignores = ignores_from_env()
    assert ignores.is_ignored("node_modules/pkg/index.js")
    assert not ignores.is_ignored("src/index.js")


@pytest.mark.parametrize(
    ("patterns", "rel_path", "expected_code"),
    [
        ("", "src/a.py", 1),
        ("build/", "build/out.txt", 0),
        ("build/", "src/a.py", 1),
    ],
)
def test_ignore_main_exit_codes(monkeypatch, patterns, rel_path, expected_code):
    monkeypatch.setenv("SHIPGATE_IGNORE_PATHS", patterns)
    assert main([rel_path]) == expected_code


def test_ignore_module_invocation(monkeypatch):
    monkeypatch.setenv("SHIPGATE_IGNORE_PATHS", "tmp/")
    result = run_command(
        [sys.executable, "-m", "shipgate.gates.ignore", "tmp/cache.txt"],
    )
    assert result.returncode == 0


def test_ignore_env_includes_gitignore(tmp_path: Path):
    (tmp_path / ".gitignore").write_text("vendor/\n", encoding="utf-8")
    env = ignore_env(tmp_path)
    patterns = env["SHIPGATE_IGNORE_PATHS"].splitlines()
    assert "vendor/" in patterns
    assert ".shipgate/" in patterns
