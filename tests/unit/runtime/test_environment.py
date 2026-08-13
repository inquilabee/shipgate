import os

from shipgate.runtime.environment import filter_environ, find_in_bin_dir


def test_managed_environment_prepends_src_on_src_layout(tmp_path, monkeypatch):
    from shipgate.runtime.environment import managed_environment

    monkeypatch.delenv("PYTHONPATH", raising=False)
    pkg = tmp_path / "src" / "demo"
    pkg.mkdir(parents=True)
    (pkg / "__init__.py").write_text("", encoding="utf-8")
    environment = managed_environment(tmp_path)
    assert environment.env["PYTHONPATH"] == str((tmp_path / "src").resolve())


def test_managed_environment_preserves_existing_pythonpath(tmp_path, monkeypatch):
    from shipgate.runtime.environment import managed_environment

    monkeypatch.setenv("PYTHONPATH", "/other")
    pkg = tmp_path / "src" / "demo"
    pkg.mkdir(parents=True)
    (pkg / "__init__.py").write_text("", encoding="utf-8")
    environment = managed_environment(tmp_path)
    parts = environment.env["PYTHONPATH"].split(os.pathsep)
    assert parts[0] == str((tmp_path / "src").resolve())
    assert "/other" in parts


def test_managed_environment_flat_layout_does_not_set_src_pythonpath(tmp_path, monkeypatch):
    from shipgate.runtime.environment import managed_environment

    monkeypatch.delenv("PYTHONPATH", raising=False)
    pkg = tmp_path / "pkg"
    pkg.mkdir()
    (pkg / "__init__.py").write_text("", encoding="utf-8")
    environment = managed_environment(tmp_path)
    assert "PYTHONPATH" not in environment.env


def test_find_in_bin_dir_rejects_parent_escape(tmp_path):
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    (bin_dir / "ruff").write_text("", encoding="utf-8")
    (tmp_path / "evil").write_text("", encoding="utf-8")
    assert find_in_bin_dir(bin_dir, "ruff") == str((bin_dir / "ruff").resolve())
    assert find_in_bin_dir(bin_dir, "../evil") is None
    assert find_in_bin_dir(bin_dir, "/etc/passwd") is None


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
