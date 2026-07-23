import os

from shipgate.runtime.environment import filter_environ


def test_filter_environ_drops_secret_like_keys(monkeypatch):
    monkeypatch.setenv("GITHUB_TOKEN", "secret")
    monkeypatch.setenv("MY_PASSWORD", "x")
    monkeypatch.setenv("PATH", "/usr/bin")
    monkeypatch.setenv("SHIPGATE_ROOT", "/repo")
    filtered = filter_environ(dict(os.environ))
    assert "GITHUB_TOKEN" not in filtered
    assert "MY_PASSWORD" not in filtered
    assert "PATH" in filtered
    assert filtered["SHIPGATE_ROOT"] == "/repo"
