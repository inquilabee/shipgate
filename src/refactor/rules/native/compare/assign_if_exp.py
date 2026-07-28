"""Native rule for ``assign-if-exp`` (Ruff SIM108 + return-if-exp)."""

from __future__ import annotations

from typing import TYPE_CHECKING

import libcst as cst

from refactor.cst_util import single_small_stmt
from refactor.rules.native.stmt_base import BodySequenceRewriteRule
from refactor.rules.native.stmt_helpers import single_terminal_stmt

if TYPE_CHECKING:
    from collections.abc import Sequence


class AssignIfExpRule(BodySequenceRewriteRule):
    rule_id = "assign-if-exp"
    summary = "Assign if expression"
    message = "Replace if statement with if expression"

    @classmethod
    def match_body(
        cls,
        body: Sequence[cst.BaseStatement],
    ) -> tuple[Sequence[cst.BaseStatement], Sequence[cst.BaseStatement]] | None:
        match = cls.return_if_exp(body)
        return match if match is not None else cls.assign_if_exp(body)

    @classmethod
    def return_if_exp(
        cls,
        body: Sequence[cst.BaseStatement],
    ) -> tuple[Sequence[cst.BaseStatement], Sequence[cst.BaseStatement]] | None:
        for index, if_stmt in enumerate(body[:-1]):
            following = body[index + 1]
            if not isinstance(if_stmt, cst.If) or if_stmt.orelse is not None:
                continue
            if cls.test_has_named_expr(if_stmt.test):
                continue
            if not isinstance(if_stmt.body, cst.IndentedBlock):
                continue
            terminal = single_terminal_stmt(if_stmt.body)
            if terminal is None or not isinstance(terminal, cst.Return):
                continue
            if cls.is_none_return(terminal) and cls.has_prior_none_guard(body, index):
                continue
            follow_return = cls.following_return(following)
            if follow_return is None:
                continue
            then_value = cls.return_branch_value(terminal)
            return (
                [if_stmt, following],
                [
                    cst.SimpleStatementLine(
                        body=[
                            cst.Return(
                                value=cst.IfExp(
                                    test=if_stmt.test,
                                    body=then_value,
                                    orelse=cls.return_branch_value_expr(follow_return),
                                ),
                            ),
                        ],
                    ),
                ],
            )
        return None

    @classmethod
    def assign_if_exp(
        cls,
        body: Sequence[cst.BaseStatement],
    ) -> tuple[Sequence[cst.BaseStatement], Sequence[cst.BaseStatement]] | None:
        for node in body:
            if not isinstance(node, cst.If) or not isinstance(node.orelse, cst.Else):
                continue
            if not isinstance(node.body, cst.IndentedBlock):
                continue
            then_assign = cls.single_assign(node.body)
            orelse_body = node.orelse.body
            if not isinstance(orelse_body, cst.IndentedBlock):
                continue
            else_assign = cls.single_assign(orelse_body)
            if then_assign is None or else_assign is None:
                continue
            if len(then_assign.targets) != 1 or len(else_assign.targets) != 1:
                continue
            if not then_assign.targets[0].target.deep_equals(else_assign.targets[0].target):
                continue
            return (
                [node],
                [
                    cst.SimpleStatementLine(
                        body=[
                            then_assign.with_changes(
                                value=cst.IfExp(
                                    test=node.test,
                                    body=then_assign.value,
                                    orelse=else_assign.value,
                                ),
                            ),
                        ],
                    ),
                ],
            )
        return None

    @staticmethod
    def single_assign(block: cst.IndentedBlock) -> cst.Assign | None:
        stmt = single_small_stmt(block)
        return stmt if isinstance(stmt, cst.Assign) else None

    @staticmethod
    def is_none_return(ret: cst.Return) -> bool:
        return ret.value is None or (isinstance(ret.value, cst.Name) and ret.value.value == "None")

    @staticmethod
    def has_prior_none_guard(
        body: Sequence[cst.BaseStatement],
        index: int,
    ) -> bool:
        for prior in body[:index]:
            if not isinstance(prior, cst.If) or prior.orelse is not None:
                continue
            if not isinstance(prior.body, cst.IndentedBlock):
                continue
            terminal = single_terminal_stmt(prior.body)
            if terminal is None or not isinstance(terminal, cst.Return):
                continue
            if AssignIfExpRule.is_none_return(terminal):
                return True
        return False

    @staticmethod
    def test_has_named_expr(test: cst.BaseExpression) -> bool:
        return (
            True
            if isinstance(test, cst.NamedExpr)
            else (
                AssignIfExpRule.test_has_named_expr(test.expression)
                if isinstance(test, cst.UnaryOperation)
                else (
                    AssignIfExpRule.test_has_named_expr(test.left)
                    or AssignIfExpRule.test_has_named_expr(
                        test.right,
                    )
                    if isinstance(test, cst.BooleanOperation)
                    else (
                        AssignIfExpRule.test_has_named_expr(test.left)
                        or any(
                            AssignIfExpRule.test_has_named_expr(comp.comparator)
                            for comp in test.comparisons
                        )
                        if isinstance(test, cst.Comparison)
                        else (
                            any(AssignIfExpRule.test_has_named_expr(arg.value) for arg in test.args)
                            if isinstance(test, cst.Call)
                            else (
                                AssignIfExpRule.test_has_named_expr(test.value)
                                if isinstance(test, cst.Attribute)
                                else False
                            )
                        )
                    )
                )
            )
        )

    @staticmethod
    def following_return(stmt: cst.BaseStatement) -> cst.BaseExpression | None:
        if not isinstance(stmt, cst.SimpleStatementLine) or len(stmt.body) != 1:
            return None
        small = stmt.body[0]
        return AssignIfExpRule.return_branch_value(small) if isinstance(small, cst.Return) else None

    @staticmethod
    def return_branch_value(ret: cst.Return) -> cst.BaseExpression:
        return (
            cst.Name("None")
            if ret.value is None
            else AssignIfExpRule.return_branch_value_expr(ret.value)
        )

    @staticmethod
    def return_branch_value_expr(value: cst.BaseExpression) -> cst.BaseExpression:
        return (
            value.with_changes(lpar=[cst.LeftParen()], rpar=[cst.RightParen()])
            if isinstance(value, (cst.Tuple, cst.IfExp))
            else value
        )
