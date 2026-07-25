from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from fastapi.testclient import TestClient

from tests.frontend.support.seed import (
    DEFAULT_RUN_ID,
    make_seeded_client,
    prepare_frontend_root,
)

if TYPE_CHECKING:
    from pathlib import Path


@pytest.fixture
def frontend_root(tmp_path: Path) -> Path:
    return prepare_frontend_root(tmp_path)


@pytest.fixture
def seeded_client(tmp_path: Path) -> TestClient:
    return make_seeded_client(tmp_path)


@pytest.fixture
def seeded_client_with_baseline(tmp_path: Path) -> TestClient:
    return make_seeded_client(tmp_path, with_baseline=True)


@pytest.fixture
def run_id() -> str:
    return DEFAULT_RUN_ID
