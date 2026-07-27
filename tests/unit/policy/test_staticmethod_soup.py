from __future__ import annotations

from shipgate.policy.core.finding import FindingLocation
from shipgate.policy.staticmethod_soup import StaticmethodSoupGate


def test_flags_class_with_only_staticmethods() -> None:
    source = (
        "class Soup:\n"
        "    @staticmethod\n"
        "    def a():\n"
        "        return 1\n"
        "    @staticmethod\n"
        "    def b():\n"
        "        return 2\n"
    )
    findings = StaticmethodSoupGate.findings_for_source("m.py", source)
    assert len(findings) == 1
    assert findings[0].rule_id == "staticmethod-soup"
    assert findings[0].location == FindingLocation(file="m.py", line=1)
    assert "Soup" in findings[0].message


def test_ignores_empty_class() -> None:
    assert StaticmethodSoupGate.findings_for_source("m.py", "class Empty:\n    pass\n") == []


def test_ignores_mixed_instance_method() -> None:
    source = (
        "class Mixed:\n"
        "    @staticmethod\n"
        "    def a():\n"
        "        return 1\n"
        "    def b(self):\n"
        "        return 2\n"
    )
    assert StaticmethodSoupGate.findings_for_source("m.py", source) == []


def test_ignores_classmethod_mix() -> None:
    source = (
        "class Mixed:\n"
        "    @staticmethod\n"
        "    def a():\n"
        "        return 1\n"
        "    @classmethod\n"
        "    def b(cls):\n"
        "        return 2\n"
    )
    assert StaticmethodSoupGate.findings_for_source("m.py", source) == []


def test_flags_single_staticmethod() -> None:
    source = "class One:\n    @staticmethod\n    def only():\n        return 1\n"
    findings = StaticmethodSoupGate.findings_for_source("m.py", source)
    assert len(findings) == 1
    assert "1 method" in findings[0].message


def test_nested_soup_class_flagged() -> None:
    source = (
        "class Outer:\n"
        "    def ok(self):\n"
        "        return 1\n"
        "    class Inner:\n"
        "        @staticmethod\n"
        "        def only():\n"
        "            return 2\n"
    )
    findings = StaticmethodSoupGate.findings_for_source("m.py", source)
    assert len(findings) == 1
    assert "Inner" in findings[0].message
