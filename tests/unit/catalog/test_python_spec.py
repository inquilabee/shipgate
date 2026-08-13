import sys

import pytest

from shipgate.catalog.core.python_spec import PythonVersionSpec, host_python_minor


def test_python_version_spec_matches_range():
    spec = PythonVersionSpec.parse(">=3.11,<3.14")
    assert spec.matches((3, 11))
    assert spec.matches((3, 13))
    assert not spec.matches((3, 14))
    assert not spec.matches((3, 10))


def test_python_version_spec_unsupported_message():
    spec = PythonVersionSpec.parse(">=3.11,<3.14")
    assert spec.unsupported_message("deadcode.check", (3, 13)) is None
    message = spec.unsupported_message("deadcode.check", (3, 14))
    assert message == (
        "deadcode.check does not support Python 3.14 (requires_python: >=3.11,<3.14)"
    )


def test_python_version_spec_rejects_empty_and_bare_version():
    with pytest.raises(ValueError, match="empty"):
        PythonVersionSpec.parse("")
    with pytest.raises(ValueError, match="invalid"):
        PythonVersionSpec.parse("3.14")
    with pytest.raises(ValueError, match="invalid"):
        PythonVersionSpec.parse(">=3.11.0")


def test_host_python_minor_matches_sys(monkeypatch):
    monkeypatch.setattr(sys, "version_info", (3, 12, 9, "final", 0))
    assert host_python_minor() == (3, 12)
