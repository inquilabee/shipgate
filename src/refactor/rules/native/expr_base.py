"""Shared bases for suggest-only native rewrite rules."""

from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar, cast

import libcst as cst

from refactor.call_match import (
    adjacent_and_comparisons,
    not_operation,
)
from refactor.cst_util import (
    BodyStatement,
    HitCollector,
    body_cleanup_hit,
    detect_with_visitor,
    expr_replacement_hit,
    noop_apply,
)
from refactor.protocol import ApplyMode, RuleKind

if TYPE_CHECKING:
    from collections.abc import Sequence

    from refactor.protocol import Hit


class SuggestOnlyExprRule:
    """Base: detect via ``match``; default policy is hint (not auto-applied)."""

    rule_id: str
    summary: str
    message: str
    kind = RuleKind.REFACTOR
    apply_mode = ApplyMode.HINT
    enabled: ClassVar[bool] = True

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
        self.record_hit(rule.hit_for(node, replacement, self.path), node)
        return True

    return type(f"{rule.__name__}Finder", (HitCollector,), {visit_name: visit})


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
    pair = adjacent_and_comparisons(node)
    if pair is None:
        return None
    left, right = pair
    left_target = left.comparisons[0]
    if not left_target.comparator.deep_equals(right.left):
        return None
    return cst.Comparison(
        left=left.left,
        comparisons=[left_target, right.comparisons[0]],
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
    not_node = not_operation(node)
    if not_node is None or not isinstance(not_node.expression, cst.Call):
        return None
    call = not_node.expression
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
                    elements=[
                        cst.Element(value=left_type),
                        cst.Element(value=right_type),
                    ],
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
    ) -> tuple[cst.BaseStatement, Sequence[BodyStatement]] | None:
        raise NotImplementedError

    @classmethod
    def finder_type(cls) -> type[HitCollector]:
        rule = cls

        class Finder(HitCollector):
            def __init__(self, *, path: str) -> None:
                super().__init__(path=path)

            def visit_Module(self, node: cst.Module) -> bool:  # ruff:ignore[invalid-function-name]
                self.check_body(node.body)
                return True

            def visit_IndentedBlock(  # ruff:ignore[invalid-function-name]
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
                stmt, cleaned = match
                self.record_hit(
                    body_cleanup_hit(
                        rule_id=rule.rule_id,
                        message=rule.message,
                        path=self.path,
                        stmt=stmt,
                        cleaned_body=cleaned,
                    ),
                    stmt,
                )

        Finder.__name__ = f"{cls.__name__}Finder"
        Finder.__qualname__ = Finder.__name__
        return Finder
