"""Shared helpers for GPSG native rules."""

from __future__ import annotations

import re
from pathlib import PurePath
from typing import TYPE_CHECKING

import libcst as cst

from refactor.cst_util import make_hit

if TYPE_CHECKING:
    from collections.abc import Sequence

    from refactor.protocol import Hit

TEST_PATH_RE = re.compile(r"(^|/)(test_[^/]+|_test)\.py$")
TYPE_SUFFIX_RE = re.compile(r"_(dict|list|set|int|float|str)$")
SNAKE_RE = re.compile(r"^_?[a-z][a-z0-9]*(_[a-z0-9]+)*$")


def is_test_path(path: str) -> bool:
    return TEST_PATH_RE.search(PurePath(path).as_posix()) is not None


def is_init_path(path: str) -> bool:
    return PurePath(path).name == "__init__.py"


def leading_string_expr(
    body: Sequence[cst.BaseStatement] | Sequence[cst.BaseSmallStatement],
) -> str | None:
    if not body:
        return None
    first = body[0]
    if isinstance(first, cst.SimpleStatementLine):
        if len(first.body) != 1:
            return None
        stmt: cst.CSTNode = first.body[0]
    else:
        stmt = first
    return (
        stmt.value.value
        if isinstance(stmt, cst.Expr) and isinstance(stmt.value, cst.SimpleString)
        else None
    )


def module_docstring(module: cst.Module) -> str | None:
    return leading_string_expr(module.body) if module.body else None


def function_docstring(node: cst.FunctionDef) -> str | None:
    return leading_string_expr(node.body.body)


def class_docstring(node: cst.ClassDef) -> str | None:
    return leading_string_expr(node.body.body)


def code_span(node: cst.CSTNode) -> str:
    return cst.Module([]).code_for_node(node)


def hit_at(
    *,
    rule_id: str,
    message: str,
    path: str,
    node: cst.CSTNode,
    before: str | None = None,
    after: str | None = None,
) -> Hit:
    snippet = before if before is not None else code_span(node)
    return make_hit(
        rule_id=rule_id,
        message=message,
        path=path,
        before=snippet,
        after=after if after is not None else snippet,
    )


def is_snake_case(name: str) -> bool:
    return (
        True
        if name.startswith("__") and name.endswith("__")
        else SNAKE_RE.fullmatch(name) is not None
    )


def is_upper_camel_case(name: str) -> bool:
    if not name:
        return False
    body = name[1:] if name.startswith("_") else name
    return (
        False
        if not body or "_" in body or not body[0].isupper() or not body.isalnum()
        else not (body.isupper() and len(body) > 1)
    )


def statement_count(body: cst.BaseSuite) -> int:
    return len(body.body) if isinstance(body, cst.IndentedBlock) else 1
