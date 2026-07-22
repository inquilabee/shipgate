import subprocess
import sys

import pytest
from shipgate.gates.ignore import EffectiveIgnores, ignores_from_env, main, patterns_from_env


def test_effective_ignores_matches_gitignore_patterns():
    ignores = EffectiveIgnores(path_patterns=("build/", "*.pyc"))
    assert ignores.is_ignored("build/output.txt")
    assert ignores.is_ignored("src/module.pyc")
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
    result = subprocess.run(
        [sys.executable, "-m", "shipgate.gates.ignore", "tmp/cache.txt"],
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
