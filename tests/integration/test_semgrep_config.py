import shutil
import subprocess
import sys
from importlib import resources
from pathlib import Path

import pytest

SEMGRP = Path(sys.executable).parent / "semgrep"
if not SEMGRP.is_file():
    SEMGRP = shutil.which("semgrep")
    SEMGRP = Path(SEMGRP) if SEMGRP else None


@pytest.mark.integration
@pytest.mark.skipif(SEMGRP is None, reason="semgrep not on PATH")
def test_bundled_semgrep_config_validates():
    bundled = resources.files("shipgate.catalog.bundled")
    config_path = Path(str(bundled / "configs" / "semgrep.yaml"))
    result = subprocess.run(
        [str(SEMGRP), "--validate", "--config", str(config_path)],
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr or result.stdout
