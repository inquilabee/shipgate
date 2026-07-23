from pathlib import Path

import pytest

from shipgate.frontend.web.app import contained_file
from shipgate.frontend.web.security import warn_if_non_loopback


def test_resolved_log_path_rejects_traversal(tmp_path: Path):
    root = tmp_path / "wt"
    root.mkdir()
    secret = tmp_path / "secret.txt"
    secret.write_text("nope", encoding="utf-8")
    with pytest.raises(ValueError):
        contained_file(root, "../secret.txt")


def test_contained_file_returns_existing_file(tmp_path: Path):
    root = tmp_path / "wt"
    root.mkdir()
    log = root / "out.txt"
    log.write_text("ok\n", encoding="utf-8")
    assert contained_file(root, "out.txt") == log.resolve()


def test_serve_warns_on_non_loopback_host(capsys):
    warn_if_non_loopback("0.0.0.0")  # noqa: S104
    assert "0.0.0.0" in capsys.readouterr().err  # noqa: S104
