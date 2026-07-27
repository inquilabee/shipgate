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
        _ = self
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
    def match(cls, node: cst.Call) -> cst.BaseExpression | None:
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
    def match(cls, node: cst.BinaryOperation) -> cst.BaseExpression | None:
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


class SubscriptRewriteRule(SuggestOnlyExprRule):
    """Rewrite matching ``cst.Subscript`` nodes."""

    @classmethod
    def match(cls, node: cst.Subscript) -> cst.BaseExpression | None:
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
    def match(cls, node: cst.FormattedString) -> cst.BaseExpression | None:
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
