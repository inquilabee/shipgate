"""Shared bases for suggest-only native statement rewrite rules."""

from __future__ import annotations

from typing import TYPE_CHECKING, cast

import libcst as cst

from refactor.cst_util import (
    HitCollector,
    ModuleAndIndentedBlockCollector,
    single_small_stmt,
    small_stmt_replacement_hit,
    stmt_replacement_hit,
    stmts_replacement_hit,
)
from refactor.rules.native.expr_base import SuggestOnlyExprRule

if TYPE_CHECKING:
    from collections.abc import Sequence

    from refactor.cst_util import BodyStatement
    from refactor.protocol import Hit


class StatementRewriteRule(SuggestOnlyExprRule):
    """Base: suggest replacement for matching statements, never auto-apply."""

    @classmethod
    def match_stmt(
        cls,
        node: cst.CSTNode,
    ) -> cst.BaseStatement | Sequence[cst.BaseStatement] | None:
        raise NotImplementedError

    @classmethod
    def finder_type(cls) -> type[HitCollector]:
        raise NotImplementedError

    @classmethod
    def stmt_hit_for(
        cls,
        node: cst.CSTNode,
        replacement: cst.BaseStatement | Sequence[cst.BaseStatement],
        path: str,
    ) -> Hit:
        return stmt_replacement_hit(
            rule_id=cls.rule_id,
            message=cls.message,
            path=path,
            before_stmt=cast("cst.BaseStatement", node),
            after_stmt=cast("BodyStatement | Sequence[BodyStatement]", replacement),
        )


def stmt_finder_type(
    rule: type[StatementRewriteRule],
    visit_name: str,
) -> type[HitCollector]:
    def visit(self: HitCollector, node: cst.CSTNode) -> bool:
        replacement = rule.match_stmt(node)
        if replacement is None:
            return True
        self.hits.append(rule.stmt_hit_for(node, replacement, self.path))
        return True

    finder = type(f"{rule.__name__}Finder", (HitCollector,), {visit_name: visit})
    return cast("type[HitCollector]", finder)


class IfRewriteRule(StatementRewriteRule):
    """Rewrite matching ``cst.If`` statements."""

    @classmethod
    def finder_type(cls) -> type[HitCollector]:
        return stmt_finder_type(cls, "visit_If")


class ForRewriteRule(StatementRewriteRule):
    """Rewrite matching ``cst.For`` statements."""

    @classmethod
    def finder_type(cls) -> type[HitCollector]:
        return stmt_finder_type(cls, "visit_For")


class WhileRewriteRule(StatementRewriteRule):
    """Rewrite matching ``cst.While`` statements."""

    @classmethod
    def finder_type(cls) -> type[HitCollector]:
        return stmt_finder_type(cls, "visit_While")


class TryRewriteRule(StatementRewriteRule):
    """Rewrite matching ``cst.Try`` statements."""

    @classmethod
    def finder_type(cls) -> type[HitCollector]:
        return stmt_finder_type(cls, "visit_Try")


class SimpleStatementLineRewriteRule(StatementRewriteRule):
    """Rewrite matching single-small-statement lines."""

    @classmethod
    def match_small_stmt(cls, node: cst.BaseSmallStatement) -> cst.BaseSmallStatement | None:
        raise NotImplementedError

    @classmethod
    def match_stmt(cls, node: cst.CSTNode) -> cst.BaseStatement | None:
        if not isinstance(node, cst.SimpleStatementLine) or len(node.body) != 1:
            return None
        replacement = cls.match_small_stmt(node.body[0])
        return None if replacement is None else node.with_changes(body=[replacement])

    @classmethod
    def stmt_hit_for(
        cls,
        node: cst.CSTNode,
        replacement: cst.BaseStatement | Sequence[cst.BaseStatement],
        path: str,
    ) -> Hit:
        if isinstance(node, cst.SimpleStatementLine) and isinstance(
            replacement,
            cst.SimpleStatementLine,
        ):
            return small_stmt_replacement_hit(
                rule_id=cls.rule_id,
                message=cls.message,
                path=path,
                before_stmt=node.body[0],
                after_stmt=replacement.body[0],
            )
        return super().stmt_hit_for(node, replacement, path)

    @classmethod
    def finder_type(cls) -> type[HitCollector]:
        return stmt_finder_type(cls, "visit_SimpleStatementLine")


class BodySequenceRewriteRule(StatementRewriteRule):
    """Suggest replacements that span adjacent statements in a body."""

    @classmethod
    def match_body(
        cls,
        body: Sequence[cst.BaseStatement],
    ) -> tuple[Sequence[cst.BaseStatement], Sequence[cst.BaseStatement]] | None:
        raise NotImplementedError

    @classmethod
    def finder_type(cls) -> type[HitCollector]:
        rule = cls

        class Finder(ModuleAndIndentedBlockCollector):
            def __init__(self, *, path: str) -> None:
                super().__init__(path=path, checker=self.check_body)

            @staticmethod
            def check_body(
                body: Sequence[cst.BaseStatement],
                hits: list[Hit],
                path: str,
            ) -> None:
                match = rule.match_body(body)
                if match is None:
                    return
                before, after = match
                hits.append(
                    stmts_replacement_hit(
                        rule_id=rule.rule_id,
                        message=rule.message,
                        path=path,
                        before_stmts=before,
                        after_stmts=cast("Sequence[BodyStatement]", after),
                    ),
                )

        Finder.__name__ = f"{cls.__name__}Finder"
        Finder.__qualname__ = Finder.__name__
        return Finder


def merge_adjacent_ifs_with_same_test(
    body: Sequence[cst.BaseStatement],
) -> tuple[Sequence[cst.BaseStatement], Sequence[cst.BaseStatement]] | None:
    for index, left in enumerate(body[:-1]):
        right = body[index + 1]
        if not isinstance(left, cst.If) or not isinstance(right, cst.If):
            continue
        if left.orelse is not None or right.orelse is not None:
            continue
        if not isinstance(left.body, cst.IndentedBlock) or not isinstance(
            right.body,
            cst.IndentedBlock,
        ):
            continue
        if not left.test.deep_equals(right.test):
            continue
        return (
            [left, right],
            [
                left.with_changes(
                    body=left.body.with_changes(body=[*left.body.body, *right.body.body]),
                ),
            ],
        )
    return None


class ReturnAssignedExpressionRule(BodySequenceRewriteRule):
    """Replace ``name = expr; return name`` with ``return expr``."""

    @classmethod
    def match_body(
        cls,
        body: Sequence[cst.BaseStatement],
    ) -> tuple[Sequence[cst.BaseStatement], Sequence[cst.BaseStatement]] | None:
        for index, assign_stmt in enumerate(body[:-1]):
            return_stmt = body[index + 1]
            assignment = cls.name_assign_stmt(assign_stmt)
            returned_name = cls.return_name_stmt(return_stmt)
            if assignment is None or returned_name is None:
                continue
            target_name, value = assignment
            if target_name != returned_name:
                continue
            return (
                [assign_stmt, return_stmt],
                [cst.SimpleStatementLine(body=[cst.Return(value=value)])],
            )
        return None

    @staticmethod
    def name_assign_stmt(stmt: cst.BaseStatement) -> tuple[str, cst.BaseExpression] | None:
        if not isinstance(stmt, cst.SimpleStatementLine) or len(stmt.body) != 1:
            return None
        assign = stmt.body[0]
        if not isinstance(assign, cst.Assign) or len(assign.targets) != 1:
            return None
        target = assign.targets[0].target
        return (target.value, assign.value) if isinstance(target, cst.Name) else None

    @staticmethod
    def return_name_stmt(stmt: cst.BaseStatement) -> str | None:
        if not isinstance(stmt, cst.SimpleStatementLine) or len(stmt.body) != 1:
            return None
        return_stmt = stmt.body[0]
        if not isinstance(return_stmt, cst.Return) or not isinstance(return_stmt.value, cst.Name):
            return None
        return return_stmt.value.value


class ClassFunctionFirstArgRule(StatementRewriteRule):
    """Suggest renaming a method's first parameter inside classes."""

    expected_arg_name: str
    required_decorator: str | None = None
    forbidden_decorators = frozenset({"staticmethod", "classmethod"})

    @classmethod
    def match_function(cls, node: cst.FunctionDef) -> cst.FunctionDef | None:
        decorators = {cls.decorator_name(decorator) for decorator in node.decorators}
        if cls.required_decorator is not None and cls.required_decorator not in decorators:
            return None
        if cls.required_decorator is None and decorators & cls.forbidden_decorators:
            return None
        if not node.params.params:
            return None
        first_param = node.params.params[0]
        if first_param.name.value == cls.expected_arg_name:
            return None
        return node.with_changes(
            params=node.params.with_changes(
                params=[
                    first_param.with_changes(name=cst.Name(cls.expected_arg_name)),
                    *node.params.params[1:],
                ],
            ),
        )

    @staticmethod
    def decorator_name(decorator: cst.Decorator) -> str | None:
        expression = decorator.decorator
        if isinstance(expression, cst.Name):
            return expression.value
        if isinstance(expression, cst.Attribute):
            return expression.attr.value
        return None

    @classmethod
    def finder_type(cls) -> type[HitCollector]:
        rule = cls

        class Finder(HitCollector):
            def __init__(self, *, path: str) -> None:
                super().__init__(path=path)
                self.class_depth = 0

            def visit_ClassDef(self, node: cst.ClassDef) -> bool:  # ruff:ignore[invalid-function-name]
                _ = node
                self.class_depth += 1
                return True

            def leave_ClassDef(self, original_node: cst.ClassDef) -> None:  # ruff:ignore[invalid-function-name]
                _ = original_node
                self.class_depth -= 1

            def visit_FunctionDef(self, node: cst.FunctionDef) -> bool:  # ruff:ignore[invalid-function-name]
                if self.class_depth == 0:
                    return True
                replacement = rule.match_function(node)
                if replacement is None:
                    return True
                self.hits.append(rule.stmt_hit_for(node, replacement, self.path))
                return True

        Finder.__name__ = f"{cls.__name__}Finder"
        Finder.__qualname__ = Finder.__name__
        return Finder


def merge_nested_if(node: cst.CSTNode) -> cst.BaseStatement | None:
    if not isinstance(node, cst.If) or node.orelse is not None:
        return None
    if not isinstance(node.body, cst.IndentedBlock) or len(node.body.body) != 1:
        return None
    inner = node.body.body[0]
    if not isinstance(inner, cst.If):
        return None
    return node.with_changes(
        test=cst.BooleanOperation(left=node.test, operator=cst.And(), right=inner.test),
        body=inner.body,
        orelse=inner.orelse,
    )


def negated_expr(expr: cst.BaseExpression) -> cst.BaseExpression:
    if isinstance(expr, cst.UnaryOperation) and isinstance(expr.operator, cst.Not):
        return expr.expression
    return cst.UnaryOperation(operator=cst.Not(), expression=expr)


def single_terminal_stmt(block: cst.IndentedBlock) -> cst.BaseSmallStatement | None:
    if len(block.body) != 1:
        return None
    line = block.body[0]
    if not isinstance(line, cst.SimpleStatementLine) or len(line.body) != 1:
        return None
    stmt = line.body[0]
    if isinstance(stmt, cst.Return | cst.Raise | cst.Break | cst.Continue):
        return stmt
    return None


def dict_update_to_union_stmt(node: cst.BaseSmallStatement) -> cst.BaseSmallStatement | None:
    if not isinstance(node, cst.Expr) or not isinstance(node.value, cst.Call):
        return None
    call = node.value
    if len(call.args) != 1 or call.args[0].keyword is not None:
        return None
    if not isinstance(call.func, cst.Attribute) or call.func.attr.value != "update":
        return None
    if not isinstance(call.func.value, cst.Name | cst.Attribute | cst.Subscript):
        return None
    return cst.AugAssign(
        target=cast("cst.BaseAssignTargetExpression", call.func.value),
        operator=cst.BitOrAssign(),
        value=call.args[0].value,
    )


def method_call_stmt(
    stmt: cst.BaseStatement,
    method_name: str,
) -> tuple[cst.BaseExpression, list[cst.Arg]] | None:
    if not isinstance(stmt, cst.SimpleStatementLine) or len(stmt.body) != 1:
        return None
    small_stmt = stmt.body[0]
    if not isinstance(small_stmt, cst.Expr) or not isinstance(small_stmt.value, cst.Call):
        return None
    call = small_stmt.value
    if not isinstance(call.func, cst.Attribute) or call.func.attr.value != method_name:
        return None
    return call.func.value, list(call.args)


def same_method_target(
    left: tuple[cst.BaseExpression, list[cst.Arg]] | None,
    right: tuple[cst.BaseExpression, list[cst.Arg]] | None,
) -> cst.BaseExpression | None:
    if left is None or right is None:
        return None
    target, _ = left
    right_target, _ = right
    return target if target.deep_equals(right_target) else None


def method_pair(
    body: Sequence[cst.BaseStatement],
    method_name: str,
) -> (
    tuple[cst.BaseStatement, cst.BaseStatement, cst.BaseExpression, list[cst.Arg], list[cst.Arg]]
    | None
):
    for index, left_stmt in enumerate(body[:-1]):
        right_stmt = body[index + 1]
        left = method_call_stmt(left_stmt, method_name)
        right = method_call_stmt(right_stmt, method_name)
        target = same_method_target(left, right)
        if target is not None and left is not None and right is not None:
            return left_stmt, right_stmt, target, left[1], right[1]
    return None


def paired_method_collection_call(
    body: Sequence[cst.BaseStatement],
    *,
    source_method: str,
    replacement_method: str,
    collection_type: type[cst.List] | type[cst.Set],
) -> tuple[Sequence[cst.BaseStatement], Sequence[cst.BaseStatement]] | None:
    pair = method_pair(body, source_method)
    if pair is None:
        return None
    left_stmt, right_stmt, target, left_args, right_args = pair
    if len(left_args) != 1 or len(right_args) != 1:
        return None
    if left_args[0].keyword is not None or right_args[0].keyword is not None:
        return None
    return (
        [left_stmt, right_stmt],
        [
            cst.SimpleStatementLine(
                body=[
                    cst.Expr(
                        value=cst.Call(
                            func=cst.Attribute(value=target, attr=cst.Name(replacement_method)),
                            args=[
                                cst.Arg(
                                    value=collection_type(
                                        elements=[
                                            cst.Element(value=left_args[0].value),
                                            cst.Element(value=right_args[0].value),
                                        ],
                                    ),
                                ),
                            ],
                        ),
                    ),
                ],
            ),
        ],
    )


def list_appends_to_extend(
    body: Sequence[cst.BaseStatement],
) -> tuple[Sequence[cst.BaseStatement], Sequence[cst.BaseStatement]] | None:
    return paired_method_collection_call(
        body,
        source_method="append",
        replacement_method="extend",
        collection_type=cst.List,
    )


def set_adds_to_update(
    body: Sequence[cst.BaseStatement],
) -> tuple[Sequence[cst.BaseStatement], Sequence[cst.BaseStatement]] | None:
    return paired_method_collection_call(
        body,
        source_method="add",
        replacement_method="update",
        collection_type=cst.Set,
    )


def name_target_for_body_stmt(
    node: cst.CSTNode,
) -> tuple[cst.Name, cst.BaseExpression, cst.BaseSmallStatement] | None:
    if not isinstance(node, cst.For) or not isinstance(node.target, cst.Name):
        return None
    if not isinstance(node.body, cst.IndentedBlock):
        return None
    stmt = single_small_stmt(node.body)
    return None if stmt is None else (node.target, node.iter, stmt)


def two_item_tuple_target(node: cst.CSTNode) -> tuple[cst.Element, cst.Element] | None:
    if not isinstance(node, cst.For) or not isinstance(node.target, cst.Tuple):
        return None
    if len(node.target.elements) != 2:
        return None
    first, second = node.target.elements
    if not isinstance(first, cst.Element) or not isinstance(second, cst.Element):
        return None
    return first, second
