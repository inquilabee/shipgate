"""Run modes."""

from enum import Enum


class RunMode(str, Enum):
    CHECK = "check"
    APPLY = "apply"
    INSTALL = "install"
