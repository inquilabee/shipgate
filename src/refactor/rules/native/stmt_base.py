"""Shared bases for suggest-only native statement rewrite rules."""

from __future__ import annotations

from typing import TYPE_CHECKING, cast

import libcst as cst

from refactor.call_match import decorator_names
from refactor.cst_util import (
    HitCollector,
    small_stmt_replacement_hit,
    stmt_replacement_hit,
    stmts_replacement_hit,
)
from refactor.rules.native.expr_base import SuggestOnlyExprRule
from refactor.rules.native.stmt_helpers import (
    dict_update_to_union_stmt,
    duplicated_if_body,
    hoist_duplicate_trailing_stmt,
    if_else_blocks,
    list_appends_to_extend,
    merge_adjacent_ifs_with_same_test,
    merge_nested_if,
    method_call_stmt,
    method_pair,
    name_target_for_body_stmt,
    negated_expr,
    paired_method_collection_call,
    same_method_target,
    set_adds_to_update,
    single_assign_block,
    single_terminal_stmt,
    two_item_tuple_target,
)
from refactor.stmt_match import (
    for_without_else_single_body,
    if_without_else_single_body,
    single_assign_from_stmt,
)

if TYPE_CHECKING:
    from collections.abc import Sequence

    from refactor.protocol import Hit

__all__ = [
    "BodySequenceRewriteRule",
    "ClassFunctionFirstArgRule",
    "ClassRewriteRule",
    "ForRewriteRule",
    "FunctionRewriteRule",
    "IfRewriteRule",
    "ReturnAssignedExpressionRule",
    "SimpleStatementLineRewriteRule",
    "StatementRewriteRule",
    "TryRewriteRule",
    "WhileRewriteRule",
    "dict_update_to_union_stmt",
    "duplicated_if_body",
    "for_without_else_single_body",
    "hoist_duplicate_trailing_stmt",
    "if_else_blocks",
    "if_without_else_single_body",
    "list_appends_to_extend",
    "merge_adjacent_ifs_with_same_test",
    "merge_nested_if",
    "method_call_stmt",
    "method_pair",
    "name_target_for_body_stmt",
    "negated_expr",
    "paired_method_collection_call",
    "same_method_target",
    "set_adds_to_update",
    "single_assign_block",
    "single_assign_from_stmt",
    "single_terminal_stmt",
    "stmt_finder_type",
    "two_item_tuple_target",
]


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
            after_stmt=replacement,
        )


def stmt_finder_type(
    rule: type[StatementRewriteRule],
    visit_name: str,
) -> type[HitCollector]:
    def visit(self: HitCollector, node: cst.CSTNode) -> bool:
        replacement = rule.match_stmt(node)
        if replacement is None:
            return True
        self.record_hit(rule.stmt_hit_for(node, replacement, self.path), node)
        return True

    return type(f"{rule.__name__}Finder", (HitCollector,), {visit_name: visit})


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


class FunctionRewriteRule(StatementRewriteRule):
    """Rewrite matching ``cst.FunctionDef`` statements."""

    @classmethod
    def finder_type(cls) -> type[HitCollector]:
        return stmt_finder_type(cls, "visit_FunctionDef")


class ClassRewriteRule(StatementRewriteRule):
    """Rewrite matching ``cst.ClassDef`` statements."""

    @classmethod
    def finder_type(cls) -> type[HitCollector]:
        return stmt_finder_type(cls, "visit_ClassDef")


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
        return (
            small_stmt_replacement_hit(
                rule_id=cls.rule_id,
                message=cls.message,
                path=path,
                before_stmt=node.body[0],
                after_stmt=replacement.body[0],
            )
            if isinstance(node, cst.SimpleStatementLine)
            and isinstance(
                replacement,
                cst.SimpleStatementLine,
            )
            else super().stmt_hit_for(node, replacement, path)
        )

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

        class Finder(HitCollector):
            def __init__(self, *, path: str) -> None:
                super().__init__(path=path)

            def visit_Module(self, node: cst.Module) -> bool:
                self.check_body(node.body)
                return True

            def visit_IndentedBlock(
                self,
                node: cst.IndentedBlock,
            ) -> bool:
                self.check_body(node.body)
                return True

            def check_body(
                self,
                body: Sequence[cst.BaseStatement],
            ) -> None:
                match = rule.match_body(body)
                if match is None:
                    return
                before, after = match
                if not before:
                    return
                self.record_hit(
                    stmts_replacement_hit(
                        rule_id=rule.rule_id,
                        message=rule.message,
                        path=self.path,
                        before_stmts=before,
                        after_stmts=after,
                    ),
                    before[0],
                )

        Finder.__name__ = f"{cls.__name__}Finder"
        Finder.__qualname__ = Finder.__name__
        return Finder


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
    def name_assign_stmt(
        stmt: cst.BaseStatement,
    ) -> tuple[str, cst.BaseExpression] | None:
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
        if not cls._rename_allowed(node.decorators):
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

    @classmethod
    def _rename_allowed(cls, decorators: Sequence[cst.Decorator]) -> bool:
        names = decorator_names(decorators)
        return (
            cls.required_decorator in names
            if cls.required_decorator is not None
            else not names & cls.forbidden_decorators
        )

    @staticmethod
    def decorator_name(decorator: cst.Decorator) -> str | None:
        expression = decorator.decorator
        return (
            expression.value
            if isinstance(expression, cst.Name)
            else (expression.attr.value if isinstance(expression, cst.Attribute) else None)
        )

    @classmethod
    def finder_type(cls) -> type[HitCollector]:
        rule = cls

        class Finder(HitCollector):
            def __init__(self, *, path: str) -> None:
                super().__init__(path=path)
                self.class_depth = 0

            def visit_ClassDef(self, node: cst.ClassDef) -> bool:
                _ = node
                self.class_depth += 1
                return True

            def leave_ClassDef(self, original_node: cst.ClassDef) -> None:
                _ = original_node
                self.class_depth -= 1

            def visit_FunctionDef(self, node: cst.FunctionDef) -> bool:
                if self.class_depth == 0:
                    return True
                replacement = rule.match_function(node)
                if replacement is None:
                    return True
                self.record_hit(rule.stmt_hit_for(node, replacement, self.path), node)
                return True

        Finder.__name__ = f"{cls.__name__}Finder"
        Finder.__qualname__ = Finder.__name__
        return Finder
