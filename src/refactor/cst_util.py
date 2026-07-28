"""Shared libcst helpers for native refactor rules."""

from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import replace
from functools import lru_cache
from pathlib import PurePath
from typing import TypeAlias, cast

import libcst as cst
from libcst.metadata import MetadataWrapper, PositionProvider

from refactor.protocol import Hit, Location, Suggestion

BodyStatement: TypeAlias = cst.SimpleStatementLine | cst.BaseCompoundStatement

BodyChecker = Callable[
    [Sequence[cst.BaseStatement], list[Hit], str],
    None,
]


class HitCollector(cst.CSTVisitor):
    """Visitor that accumulates refactor hits for a source file."""

    METADATA_DEPENDENCIES = (PositionProvider,)

    def __init__(self, *, path: str) -> None:
        self.path = path
        self.hits: list[Hit] = []

    def record_hit(self, hit: Hit, node: cst.CSTNode) -> None:
        self.hits.append(self.with_location(hit, node))

    def with_location(self, hit: Hit, node: cst.CSTNode) -> Hit:
        try:
            position = self.get_metadata(PositionProvider, node)
        except KeyError:
            return hit
        return replace(
            hit,
            location=Location(
                path=hit.location.path,
                line=position.start.line,
                column=position.start.column,
            ),
        )


def detect_with_visitor(
    source: str,
    path: str,
    visitor_cls: type[HitCollector],
) -> list[Hit]:
    module = parse_module_cached(source)
    finder = visitor_cls(path=path)
    MetadataWrapper(module, unsafe_skip_copy=True).visit(finder)
    return finder.hits


@lru_cache(maxsize=32)
def parse_module_cached(source: str) -> cst.Module:
    return cst.parse_module(source)


def noop_apply(source: str, hits: Sequence[Hit]) -> str | None:
    _ = source, hits
    return None


def apply_with_transformer(source: str, transformer: cst.CSTTransformer) -> str | None:
    """Parse *source*, run *transformer*, return new code or ``None`` if unchanged."""
    module = cst.parse_module(source)
    updated = module.visit(transformer)
    rewritten = updated.code
    return None if rewritten == source else rewritten


class ModuleAndIndentedBlockCollector(HitCollector):
    """Visit module and indented-block bodies with a shared checker."""

    def __init__(self, *, path: str, checker: BodyChecker) -> None:
        super().__init__(path=path)
        self.checker = checker

    def visit_Module(self, node: cst.Module) -> bool:  # ruff:ignore[invalid-function-name]
        self.checker(node.body, self.hits, self.path)
        return True

    def visit_IndentedBlock(  # ruff:ignore[invalid-function-name]
        self,
        node: cst.IndentedBlock,
    ) -> bool:
        self.checker(node.body, self.hits, self.path)
        return True


class IndentedBlockCollector(HitCollector):
    """Visit indented-block bodies with a shared checker."""

    def __init__(self, *, path: str, checker: BodyChecker) -> None:
        super().__init__(path=path)
        self.checker = checker

    def visit_IndentedBlock(  # ruff:ignore[invalid-function-name]
        self,
        node: cst.IndentedBlock,
    ) -> bool:
        self.checker(node.body, self.hits, self.path)
        return True


def code_for_stmts(*stmts: cst.BaseStatement) -> str:
    body = [cast("BodyStatement", stmt) for stmt in stmts]
    return cst.Module(body=body).code.strip()


def code_for_stmt(stmt: BodyStatement | cst.BaseStatement) -> str:
    return code_for_stmts(stmt)


def code_for_small_stmt(stmt: cst.BaseSmallStatement) -> str:
    return code_for_stmts(cst.SimpleStatementLine(body=[stmt]))


def code_for_expr(expr: cst.BaseExpression) -> str:
    return code_for_stmts(cst.SimpleStatementLine(body=[cst.Expr(value=expr)]))


def parse_integer_literal(value: str) -> int | None:
    """Parse a Python integer token without assuming decimal syntax."""
    try:
        return int(value.replace("_", ""), 0)
    except ValueError:
        return None


def is_test_path(path: str) -> bool:
    parsed = PurePath(path)
    return any(part in ("test", "tests") for part in parsed.parts)


def make_hit(
    *,
    rule_id: str,
    message: str,
    path: str,
    before: str,
    after: str,
    suggestion_message: str | None = None,
) -> Hit:
    return Hit(
        rule_id=rule_id,
        message=message,
        location=Location(path=path),
        suggestion=Suggestion(
            before=before,
            after=after,
            message=suggestion_message,
        ),
    )


def body_cleanup_hit(
    *,
    rule_id: str,
    message: str,
    path: str,
    stmt: cst.BaseStatement,
    cleaned_body: Sequence[BodyStatement],
) -> Hit:
    return make_hit(
        rule_id=rule_id,
        message=message,
        path=path,
        before=code_for_stmt(cast("BodyStatement", stmt)),
        after=code_for_stmts(*cleaned_body),
    )


def stmts_replacement_hit(
    *,
    rule_id: str,
    message: str,
    path: str,
    before_stmts: Sequence[cst.BaseStatement],
    after_stmts: Sequence[BodyStatement],
) -> Hit:
    return make_hit(
        rule_id=rule_id,
        message=message,
        path=path,
        before=code_for_stmts(*before_stmts),
        after=code_for_stmts(*after_stmts),
    )


def stmt_replacement_hit(
    *,
    rule_id: str,
    message: str,
    path: str,
    before_stmt: cst.BaseStatement,
    after_stmt: BodyStatement | Sequence[BodyStatement],
) -> Hit:
    after = (
        code_for_stmt(after_stmt)
        if isinstance(after_stmt, cst.BaseStatement)
        else code_for_stmts(*after_stmt)
    )
    return make_hit(
        rule_id=rule_id,
        message=message,
        path=path,
        before=code_for_stmt(cast("BodyStatement", before_stmt)),
        after=after,
    )


def small_stmt_replacement_hit(
    *,
    rule_id: str,
    message: str,
    path: str,
    before_stmt: cst.BaseSmallStatement,
    after_stmt: cst.BaseSmallStatement,
) -> Hit:
    return make_hit(
        rule_id=rule_id,
        message=message,
        path=path,
        before=code_for_small_stmt(before_stmt),
        after=code_for_small_stmt(after_stmt),
    )


def expr_replacement_hit(
    *,
    rule_id: str,
    message: str,
    path: str,
    before_expr: cst.BaseExpression,
    after_expr: cst.BaseExpression,
    suggestion_message: str | None = None,
) -> Hit:
    return make_hit(
        rule_id=rule_id,
        message=message,
        path=path,
        before=code_for_expr(before_expr),
        after=code_for_expr(after_expr),
        suggestion_message=suggestion_message,
    )


def is_name(node: cst.BaseExpression, value: str) -> bool:
    return isinstance(node, cst.Name) and node.value == value


def is_true(node: cst.BaseExpression) -> bool:
    return is_name(node, "True")


def is_false(node: cst.BaseExpression) -> bool:
    return is_name(node, "False")


def is_none_name(node: cst.BaseExpression) -> bool:
    return is_name(node, "None")


def is_empty_call(node: cst.Call, name: str) -> bool:
    return isinstance(node.func, cst.Name) and node.func.value == name and not node.args


def unwrap_str_call(expr: cst.BaseExpression) -> cst.BaseExpression | None:
    if not isinstance(expr, cst.Call):
        return None
    if not isinstance(expr.func, cst.Name) or expr.func.value != "str":
        return None
    if len(expr.args) != 1 or expr.args[0].keyword is not None:
        return None
    return expr.args[0].value


def match_named_for(
    stmt: cst.BaseStatement,
) -> tuple[cst.For, cst.BaseExpression] | None:
    if not isinstance(stmt, cst.For) or stmt.orelse:
        return None
    if not isinstance(stmt.target, cst.Name):
        return None
    if not isinstance(stmt.body, cst.IndentedBlock):
        return None
    return stmt, stmt.iter


def single_small_stmt(body: cst.IndentedBlock) -> cst.BaseSmallStatement | None:
    if len(body.body) != 1:
        return None
    inner = body.body[0]
    if not isinstance(inner, cst.SimpleStatementLine) or len(inner.body) != 1:
        return None
    return inner.body[0]


def check_single_for_named_action(
    body: Sequence[cst.BaseStatement],
    hits: list[Hit],
    path: str,
    *,
    action_name: Callable[[cst.IndentedBlock], str | None],
    build_hit: Callable[[cst.For, cst.BaseExpression, str], Hit],
) -> None:
    if len(body) != 1:
        return
    match = match_named_for(body[0])
    if match is None:
        return
    for_stmt, iterable = match
    if not isinstance(for_stmt.target, cst.Name):
        return
    target_name = for_stmt.target.value
    if not isinstance(for_stmt.body, cst.IndentedBlock):
        return
    matched_name = action_name(for_stmt.body)
    if matched_name is None or matched_name != target_name:
        return
    hits.append(build_hit(for_stmt, iterable, path))
