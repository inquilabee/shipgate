from pathlib import Path

import pytest

from shipgate.batch import BatchFileLoader, BatchRequest
from shipgate.domain.modes import RunMode
from shipgate.errors import ConfigError


def test_load_sample_batch_fixture():
    path = Path(__file__).resolve().parents[1] / "fixtures" / "batch" / "sample.yaml"
    requests = BatchFileLoader.load(path)
    assert requests == [
        BatchRequest(
            runnable="ruff.lint",
            mode=RunMode.CHECK,
            target=Path("src"),
        )
    ]


def test_batch_file_rejects_non_list(tmp_path: Path):
    path = tmp_path / "batch.yaml"
    path.write_text("runnable: ruff.lint\n", encoding="utf-8")
    with pytest.raises(ConfigError, match="list of requests"):
        BatchFileLoader.load(path)


def test_batch_file_rejects_non_mapping_item(tmp_path: Path):
    path = tmp_path / "batch.yaml"
    path.write_text("requests:\n  - ruff.lint\n", encoding="utf-8")
    with pytest.raises(ConfigError, match="must be a mapping"):
        BatchFileLoader.load(path)


def test_batch_file_rejects_missing_runnable(tmp_path: Path):
    path = tmp_path / "batch.yaml"
    path.write_text("requests:\n  - mode: check\n", encoding="utf-8")
    with pytest.raises(ConfigError, match="missing runnable"):
        BatchFileLoader.load(path)


def test_batch_file_rejects_invalid_mode(tmp_path: Path):
    path = tmp_path / "batch.yaml"
    path.write_text(
        "requests:\n  - runnable: ruff.lint\n    mode: wipe\n",
        encoding="utf-8",
    )
    with pytest.raises(ConfigError, match="invalid mode"):
        BatchFileLoader.load(path)


def test_batch_file_rejects_multiple_paths(tmp_path: Path):
    path = tmp_path / "batch.yaml"
    path.write_text(
        "requests:\n  - runnable: ruff.lint\n    options:\n      paths: [src, tests]\n",
        encoding="utf-8",
    )
    with pytest.raises(ConfigError, match="exactly one path"):
        BatchFileLoader.load(path)


def test_batch_file_empty_paths_default_to_dot(tmp_path: Path):
    path = tmp_path / "batch.yaml"
    path.write_text(
        "requests:\n  - runnable: ruff.lint\n    options:\n      paths: []\n",
        encoding="utf-8",
    )
    requests = BatchFileLoader.load(path)
    assert requests == [
        BatchRequest(runnable="ruff.lint", mode=RunMode.CHECK, target=Path()),
    ]


def test_run_batch_rejects_install_mode(tmp_path: Path):
    from shipgate.app import ShipGateApp

    path = tmp_path / "batch.yaml"
    path.write_text(
        "requests:\n  - runnable: ruff.lint\n    mode: install\n",
        encoding="utf-8",
    )
    with pytest.raises(ConfigError, match="not supported"):
        ShipGateApp().run_batch(tmp_path, path)
