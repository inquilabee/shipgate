"""Run modes."""

from enum import StrEnum


class RunMode(StrEnum):
    CHECK = "check"
    APPLY = "apply"
    INSTALL = "install"
