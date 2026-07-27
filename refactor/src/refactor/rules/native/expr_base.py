"""Shared bases for suggest-only native rewrite rules."""

from __future__ import annotations

from typing import TYPE_CHECKING, cast

import libcst as cst

from refactor.cst_util import (
    BodyStatement,
    HitCollector,
    ModuleAndIndentedBlockCollector,
    body_cleanup_hit,
    detect_with_visitor,
    expr_replacement_hit,
    noop_apply,
)
from refactor.protocol import RuleKind

if TYPE_CHECKING:
    from collections.abc import Sequence

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


class CallRewriteRule(SuggestOnlyExprRule):
    """Rewrite matching ``cst.Call`` nodes."""

    @classmethod
    def match(cls, node: cst.CSTNode) -> cst.BaseExpression | None:
        raise NotImplementedError

    @classmethod
    def finder_type(cls) -> type[HitCollector]:
        rule = cls

        class Finder(HitCollector):
            def visit_Call(  # ruff:ignore[invalid-function-name]
                self,
                node: cst.Call,
            ) -> bool:
                replacement = rule.match(node)
                if replacement is None:
                    return True
                self.hits.append(rule.hit_for(node, replacement, self.path))
                return True

        Finder.__name__ = f"{cls.__name__}Finder"
        Finder.__qualname__ = Finder.__name__
        return Finder


class BinaryOpRewriteRule(SuggestOnlyExprRule):
    """Rewrite matching ``cst.BinaryOperation`` nodes."""

    @classmethod
    def match(cls, node: cst.CSTNode) -> cst.BaseExpression | None:
        raise NotImplementedError

    @classmethod
    def finder_type(cls) -> type[HitCollector]:
        rule = cls

        class Finder(HitCollector):
            def visit_BinaryOperation(  # ruff:ignore[invalid-function-name]
                self,
                node: cst.BinaryOperation,
            ) -> bool:
                replacement = rule.match(node)
                if replacement is None:
                    return True
                self.hits.append(rule.hit_for(node, replacement, self.path))
                return True

        Finder.__name__ = f"{cls.__name__}Finder"
        Finder.__qualname__ = Finder.__name__
        return Finder


class BooleanOpRewriteRule(SuggestOnlyExprRule):
    """Rewrite matching ``cst.BooleanOperation`` nodes."""

    @classmethod
    def match(cls, node: cst.CSTNode) -> cst.BaseExpression | None:
        raise NotImplementedError

    @classmethod
    def finder_type(cls) -> type[HitCollector]:
        rule = cls

        class Finder(HitCollector):
            def visit_BooleanOperation(  # ruff:ignore[invalid-function-name]
                self,
                node: cst.BooleanOperation,
            ) -> bool:
                replacement = rule.match(node)
                if replacement is None:
                    return True
                self.hits.append(rule.hit_for(node, replacement, self.path))
                return True

        Finder.__name__ = f"{cls.__name__}Finder"
        Finder.__qualname__ = Finder.__name__
        return Finder


class UnaryOpRewriteRule(SuggestOnlyExprRule):
    """Rewrite matching ``cst.UnaryOperation`` nodes."""

    @classmethod
    def match(cls, node: cst.CSTNode) -> cst.BaseExpression | None:
        raise NotImplementedError

    @classmethod
    def finder_type(cls) -> type[HitCollector]:
        rule = cls

        class Finder(HitCollector):
            def visit_UnaryOperation(  # ruff:ignore[invalid-function-name]
                self,
                node: cst.UnaryOperation,
            ) -> bool:
                replacement = rule.match(node)
                if replacement is None:
                    return True
                self.hits.append(rule.hit_for(node, replacement, self.path))
                return True

        Finder.__name__ = f"{cls.__name__}Finder"
        Finder.__qualname__ = Finder.__name__
        return Finder


class IfExpRewriteRule(SuggestOnlyExprRule):
    """Rewrite matching ``cst.IfExp`` nodes."""

    @classmethod
    def match(cls, node: cst.CSTNode) -> cst.BaseExpression | None:
        raise NotImplementedError

    @classmethod
    def finder_type(cls) -> type[HitCollector]:
        rule = cls

        class Finder(HitCollector):
            def visit_IfExp(  # ruff:ignore[invalid-function-name]
                self,
                node: cst.IfExp,
            ) -> bool:
                replacement = rule.match(node)
                if replacement is None:
                    return True
                self.hits.append(rule.hit_for(node, replacement, self.path))
                return True

        Finder.__name__ = f"{cls.__name__}Finder"
        Finder.__qualname__ = Finder.__name__
        return Finder


class ComparisonRewriteRule(SuggestOnlyExprRule):
    """Rewrite matching ``cst.Comparison`` nodes."""

    @classmethod
    def match(cls, node: cst.CSTNode) -> cst.BaseExpression | None:
        raise NotImplementedError

    @classmethod
    def finder_type(cls) -> type[HitCollector]:
        rule = cls

        class Finder(HitCollector):
            def visit_Comparison(  # ruff:ignore[invalid-function-name]
                self,
                node: cst.Comparison,
            ) -> bool:
                replacement = rule.match(node)
                if replacement is None:
                    return True
                self.hits.append(rule.hit_for(node, replacement, self.path))
                return True

        Finder.__name__ = f"{cls.__name__}Finder"
        Finder.__qualname__ = Finder.__name__
        return Finder


class DictRewriteRule(SuggestOnlyExprRule):
    """Rewrite matching ``cst.Dict`` literal nodes."""

    @classmethod
    def match(cls, node: cst.CSTNode) -> cst.BaseExpression | None:
        raise NotImplementedError

    @classmethod
    def finder_type(cls) -> type[HitCollector]:
        rule = cls

        class Finder(HitCollector):
            def visit_Dict(  # ruff:ignore[invalid-function-name]
                self,
                node: cst.Dict,
            ) -> bool:
                replacement = rule.match(node)
                if replacement is None:
                    return True
                self.hits.append(rule.hit_for(node, replacement, self.path))
                return True

        Finder.__name__ = f"{cls.__name__}Finder"
        Finder.__qualname__ = Finder.__name__
        return Finder


class SetRewriteRule(SuggestOnlyExprRule):
    """Rewrite matching ``cst.Set`` literal nodes."""

    @classmethod
    def match(cls, node: cst.CSTNode) -> cst.BaseExpression | None:
        raise NotImplementedError

    @classmethod
    def finder_type(cls) -> type[HitCollector]:
        rule = cls

        class Finder(HitCollector):
            def visit_Set(  # ruff:ignore[invalid-function-name]
                self,
                node: cst.Set,
            ) -> bool:
                replacement = rule.match(node)
                if replacement is None:
                    return True
                self.hits.append(rule.hit_for(node, replacement, self.path))
                return True

        Finder.__name__ = f"{cls.__name__}Finder"
        Finder.__qualname__ = Finder.__name__
        return Finder


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


class SubscriptRewriteRule(SuggestOnlyExprRule):
    """Rewrite matching ``cst.Subscript`` nodes."""

    @classmethod
    def match(cls, node: cst.CSTNode) -> cst.BaseExpression | None:
        raise NotImplementedError

    @classmethod
    def finder_type(cls) -> type[HitCollector]:
        rule = cls

        class Finder(HitCollector):
            def visit_Subscript(  # ruff:ignore[invalid-function-name]
                self,
                node: cst.Subscript,
            ) -> bool:
                replacement = rule.match(node)
                if replacement is None:
                    return True
                self.hits.append(rule.hit_for(node, replacement, self.path))
                return True

        Finder.__name__ = f"{cls.__name__}Finder"
        Finder.__qualname__ = Finder.__name__
        return Finder


class FormattedStringRewriteRule(SuggestOnlyExprRule):
    """Rewrite matching ``cst.FormattedString`` nodes."""

    @classmethod
    def match(cls, node: cst.CSTNode) -> cst.BaseExpression | None:
        raise NotImplementedError

    @classmethod
    def finder_type(cls) -> type[HitCollector]:
        rule = cls

        class Finder(HitCollector):
            def visit_FormattedString(  # ruff:ignore[invalid-function-name]
                self,
                node: cst.FormattedString,
            ) -> bool:
                replacement = rule.match(node)
                if replacement is None:
                    return True
                self.hits.append(rule.hit_for(node, replacement, self.path))
                return True

        Finder.__name__ = f"{cls.__name__}Finder"
        Finder.__qualname__ = Finder.__name__
        return Finder


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
