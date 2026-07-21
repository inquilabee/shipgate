import os

from shipgate.ci import apply_ci_defaults, is_ci_environment, write_github_step_summary


def test_is_ci_environment():
    assert not is_ci_environment()
    os.environ["CI"] = "true"
    try:
        assert is_ci_environment()
    finally:
        del os.environ["CI"]


def test_apply_ci_defaults():
    os.environ["CI"] = "true"
    try:
        assert apply_ci_defaults(None) == "github"
        assert apply_ci_defaults("compact") == "compact"
    finally:
        del os.environ["CI"]


def test_write_github_step_summary(tmp_path, monkeypatch):
    summary = tmp_path / "summary.md"
    monkeypatch.setenv("GITHUB_STEP_SUMMARY", str(summary))
    write_github_step_summary("shipgate check passed")
    assert "shipgate check passed" in summary.read_text(encoding="utf-8")
