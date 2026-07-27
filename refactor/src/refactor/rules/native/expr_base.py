"""Shared bases for suggest-only native rewrite rules."""

from __future__ import annotations

from typing import TYPE_CHECKING, cast

import libcst as cst

from refactor.cst_util import (
    HitCollector,
    ModuleAndIndentedBlockCollector,
    body_cleanup_hit,
    detect_with_visitor,
    expr_replacement_hit,
    noop_apply,
    stmt_replacement_hit,
)
from refactor.protocol import RuleKind

if TYPE_CHECKING:
    from collections.abc import Sequence

    from refactor.cst_util import BodyStatement
    from refactor.protocol import Hit


class SuggestOnlyExprRule:
    """Base: detect via ``match``, never auto-apply."""

    rule_id: str
    summary: str
    message: str
    kind = RuleKind.REFACTOR
    safe_apply = False

    def detect(self, source: str, path: str) -> list[Hit]:
        return detect_with_visitor(source, path, self.finder_type())

    def apply(self, source: str, hits: Sequence[Hit]) -> str | None:
        _ = self
        return noop_apply(source, hits)

    @classmethod
    def match(cls, node: cst.CSTNode) -> cst.BaseExpression | None:
        raise NotImplementedError

    @classmethod
    def finder_type(cls) -> type[HitCollector]:
        raise NotImplementedError

    @classmethod
    def hit_for(
        cls,
        node: cst.CSTNode,
        replacement: cst.BaseExpression,
        path: str,
    ) -> Hit:
        return expr_replacement_hit(
            rule_id=cls.rule_id,
            message=cls.message,
            path=path,
            before_expr=cast("cst.BaseExpression", node),
            after_expr=replacement,
        )


def rewrite_finder_type(
    rule: type[SuggestOnlyExprRule],
    visit_name: str,
) -> type[HitCollector]:
    def visit(self: HitCollector, node: cst.CSTNode) -> bool:
        replacement = rule.match(node)
        if replacement is None:
            return True
        self.hits.append(rule.hit_for(node, replacement, self.path))
        return True

    finder = type(f"{rule.__name__}Finder", (HitCollector,), {visit_name: visit})
    return cast("type[HitCollector]", finder)


class StatementRewriteRule:
    """Base: suggest replacement for matching statements, never auto-apply."""

    rule_id: str
    summary: str
    message: str
    kind = RuleKind.REFACTOR
    safe_apply = False

    def detect(self, source: str, path: str) -> list[Hit]:
        return detect_with_visitor(source, path, self.finder_type())

    def apply(self, source: str, hits: Sequence[Hit]) -> str | None:
        _ = self
        return noop_apply(source, hits)

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
    def hit_for(
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
        self.hits.append(rule.hit_for(node, replacement, self.path))
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


class CallRewriteRule(SuggestOnlyExprRule):
    """Rewrite matching ``cst.Call`` nodes."""

    @classmethod
    def match(cls, node: cst.CSTNode) -> cst.BaseExpression | None:
        raise NotImplementedError

    @classmethod
    def finder_type(cls) -> type[HitCollector]:
        return rewrite_finder_type(cls, "visit_Call")


class BinaryOpRewriteRule(SuggestOnlyExprRule):
    """Rewrite matching ``cst.BinaryOperation`` nodes."""

    @classmethod
    def match(cls, node: cst.CSTNode) -> cst.BaseExpression | None:
        raise NotImplementedError

    @classmethod
    def finder_type(cls) -> type[HitCollector]:
        return rewrite_finder_type(cls, "visit_BinaryOperation")


class BooleanOpRewriteRule(SuggestOnlyExprRule):
    """Rewrite matching ``cst.BooleanOperation`` nodes."""

    @classmethod
    def match(cls, node: cst.CSTNode) -> cst.BaseExpression | None:
        raise NotImplementedError

    @classmethod
    def finder_type(cls) -> type[HitCollector]:
        return rewrite_finder_type(cls, "visit_BooleanOperation")


class UnaryOpRewriteRule(SuggestOnlyExprRule):
    """Rewrite matching ``cst.UnaryOperation`` nodes."""

    @classmethod
    def match(cls, node: cst.CSTNode) -> cst.BaseExpression | None:
        raise NotImplementedError

    @classmethod
    def finder_type(cls) -> type[HitCollector]:
        return rewrite_finder_type(cls, "visit_UnaryOperation")


class IfExpRewriteRule(SuggestOnlyExprRule):
    """Rewrite matching ``cst.IfExp`` nodes."""

    @classmethod
    def match(cls, node: cst.CSTNode) -> cst.BaseExpression | None:
        raise NotImplementedError

    @classmethod
    def finder_type(cls) -> type[HitCollector]:
        return rewrite_finder_type(cls, "visit_IfExp")


class ComparisonRewriteRule(SuggestOnlyExprRule):
    """Rewrite matching ``cst.Comparison`` nodes."""

    @classmethod
    def match(cls, node: cst.CSTNode) -> cst.BaseExpression | None:
        raise NotImplementedError

    @classmethod
    def finder_type(cls) -> type[HitCollector]:
        return rewrite_finder_type(cls, "visit_Comparison")


class DictRewriteRule(SuggestOnlyExprRule):
    """Rewrite matching ``cst.Dict`` literal nodes."""

    @classmethod
    def match(cls, node: cst.CSTNode) -> cst.BaseExpression | None:
        raise NotImplementedError

    @classmethod
    def finder_type(cls) -> type[HitCollector]:
        return rewrite_finder_type(cls, "visit_Dict")


class SetRewriteRule(SuggestOnlyExprRule):
    """Rewrite matching ``cst.Set`` literal nodes."""

    @classmethod
    def match(cls, node: cst.CSTNode) -> cst.BaseExpression | None:
        raise NotImplementedError

    @classmethod
    def finder_type(cls) -> type[HitCollector]:
        return rewrite_finder_type(cls, "visit_Set")


def merge_adjacent_comparisons(node: cst.CSTNode) -> cst.BaseExpression | None:
    if not isinstance(node, cst.BooleanOperation) or not isinstance(node.operator, cst.And):
        return None
    if not isinstance(node.left, cst.Comparison) or not isinstance(node.right, cst.Comparison):
        return None
    if len(node.left.comparisons) != 1 or len(node.right.comparisons) != 1:
        return None
    left_target = node.left.comparisons[0]
    if not left_target.comparator.deep_equals(node.right.left):
        return None
    return cst.Comparison(
        left=node.left.left,
        comparisons=[left_target, node.right.comparisons[0]],
    )


def or_fallback_if_exp(node: cst.CSTNode) -> cst.BaseExpression | None:
    if not isinstance(node, cst.IfExp):
        return None
    if not node.body.deep_equals(node.test):
        return None
    return cst.BooleanOperation(
        left=node.test,
        operator=cst.Or(),
        right=node.orelse,
    )


def same_branch_if_exp(node: cst.CSTNode) -> cst.BaseExpression | None:
    return node.body if isinstance(node, cst.IfExp) and node.body.deep_equals(node.orelse) else None


def swap_negated_if_exp(node: cst.CSTNode) -> cst.BaseExpression | None:
    if not isinstance(node, cst.IfExp):
        return None
    if not isinstance(node.test, cst.UnaryOperation) or not isinstance(node.test.operator, cst.Not):
        return None
    return node.with_changes(test=node.test.expression, body=node.orelse, orelse=node.body)


def invert_any_all_call(node: cst.CSTNode) -> cst.BaseExpression | None:
    if not isinstance(node, cst.UnaryOperation) or not isinstance(node.operator, cst.Not):
        return None
    if not isinstance(node.expression, cst.Call):
        return None
    call = node.expression
    if not isinstance(call.func, cst.Name) or call.func.value not in {"any", "all"}:
        return None
    if len(call.args) != 1 or call.args[0].keyword is not None:
        return None
    generator = call.args[0].value
    if not isinstance(generator, cst.GeneratorExp):
        return None
    inverted_name = "all" if call.func.value == "any" else "any"
    inverted_generator = generator.with_changes(
        elt=cst.UnaryOperation(operator=cst.Not(), expression=generator.elt),
    )
    return call.with_changes(
        func=cst.Name(inverted_name),
        args=[cst.Arg(value=inverted_generator)],
    )


def merge_isinstance_calls(node: cst.CSTNode) -> cst.BaseExpression | None:
    if not isinstance(node, cst.BooleanOperation) or not isinstance(node.operator, cst.Or):
        return None
    left = isinstance_call(node.left)
    right = isinstance_call(node.right)
    if left is None or right is None:
        return None
    subject, left_type = left
    right_subject, right_type = right
    if not subject.deep_equals(right_subject):
        return None
    return cst.Call(
        func=cst.Name("isinstance"),
        args=[
            cst.Arg(value=subject),
            cst.Arg(
                value=cst.Tuple(
                    elements=[cst.Element(value=left_type), cst.Element(value=right_type)],
                ),
            ),
        ],
    )


def isinstance_call(
    node: cst.BaseExpression,
) -> tuple[cst.BaseExpression, cst.BaseExpression] | None:
    if not isinstance(node, cst.Call):
        return None
    if not isinstance(node.func, cst.Name) or node.func.value != "isinstance":
        return None
    if len(node.args) != 2 or any(arg.keyword is not None for arg in node.args):
        return None
    return node.args[0].value, node.args[1].value


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


class SubscriptRewriteRule(SuggestOnlyExprRule):
    """Rewrite matching ``cst.Subscript`` nodes."""

    @classmethod
    def match(cls, node: cst.CSTNode) -> cst.BaseExpression | None:
        raise NotImplementedError

    @classmethod
    def finder_type(cls) -> type[HitCollector]:
        return rewrite_finder_type(cls, "visit_Subscript")


class FormattedStringRewriteRule(SuggestOnlyExprRule):
    """Rewrite matching ``cst.FormattedString`` nodes."""

    @classmethod
    def match(cls, node: cst.CSTNode) -> cst.BaseExpression | None:
        raise NotImplementedError

    @classmethod
    def finder_type(cls) -> type[HitCollector]:
        return rewrite_finder_type(cls, "visit_FormattedString")


class BodyCleanupRule(SuggestOnlyExprRule):
    """Suggest cleanup for matching statements inside module or indented bodies."""

    @classmethod
    def match_body(
        cls,
        body: Sequence[cst.BaseStatement],
    ) -> (
        tuple[
            cst.BaseStatement,
            Sequence[cst.SimpleStatementLine | cst.BaseCompoundStatement],
        ]
        | None
    ):
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
                stmt, cleaned = match
                hits.append(
                    body_cleanup_hit(
                        rule_id=rule.rule_id,
                        message=rule.message,
                        path=path,
                        stmt=stmt,
                        cleaned_body=cleaned,
                    ),
                )

        Finder.__name__ = f"{cls.__name__}Finder"
        Finder.__qualname__ = Finder.__name__
        return Finder
