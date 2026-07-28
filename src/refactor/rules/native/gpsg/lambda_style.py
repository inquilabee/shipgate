"""GPSG native: lambdas-should-be-short, filter-lambda-to-generator, no-complex-if-expressions."""

from __future__ import annotations

from typing import TYPE_CHECKING

import libcst as cst

from refactor.cst_util import HitCollector, detect_with_visitor, noop_apply
from refactor.protocol import ApplyMode, RuleKind
from refactor.rules.native.gpsg.helpers import code_span, hit_at

if TYPE_CHECKING:
    from collections.abc import Sequence

    from refactor.protocol import Hit

LAMBDA_BODY_LIMIT = 80
IF_EXP_ARM_LIMIT = 80


class LambdasShouldBeShortRule:
    rule_id = "lambdas-should-be-short"
    kind = RuleKind.SUGGESTION
    summary = "Lambda functions should be kept to a single short line"
    apply_mode = ApplyMode.HINT

    def detect(self, source: str, path: str) -> list[Hit]:
        _ = self
        return detect_with_visitor(source, path, LambdasShouldBeShortRule.Finder)

    def apply(self, source: str, hits: Sequence[Hit]) -> str | None:
        _ = self
        return noop_apply(source, hits)

    class Finder(HitCollector):
        def visit_Lambda(self, node: cst.Lambda) -> bool:  # ruff:ignore[invalid-function-name]
            body = code_span(node.body)
            if len(body) <= LAMBDA_BODY_LIMIT:
                return True
            self.record_hit(
                hit_at(
                    rule_id="lambdas-should-be-short",
                    message="Lambda functions should be kept to a single line",
                    path=self.path,
                    node=node,
                ),
                node,
            )
            return True


class FilterLambdaToGeneratorRule:
    rule_id = "filter-lambda-to-generator"
    kind = RuleKind.SUGGESTION
    summary = "Replace filtering with a lambda with a generator expression"
    apply_mode = ApplyMode.HINT

    def detect(self, source: str, path: str) -> list[Hit]:
        _ = self
        return detect_with_visitor(source, path, FilterLambdaToGeneratorRule.Finder)

    def apply(self, source: str, hits: Sequence[Hit]) -> str | None:
        _ = self
        return noop_apply(source, hits)

    class Finder(HitCollector):
        def visit_Call(self, node: cst.Call) -> bool:  # ruff:ignore[invalid-function-name]
            if not isinstance(node.func, cst.Name) or node.func.value != "filter":
                return True
            if len(node.args) != 2 or any(arg.keyword is not None for arg in node.args):
                return True
            predicate = node.args[0].value
            items = node.args[1].value
            if not isinstance(predicate, cst.Lambda):
                return True
            params = predicate.params
            if len(params.params) != 1:
                return True
            if isinstance(params.star_arg, cst.Param) or isinstance(
                params.star_kwarg,
                cst.Param,
            ):
                return True
            arg_name = params.params[0].name
            after = cst.GeneratorExp(
                elt=arg_name.deep_clone(),
                for_in=cst.CompFor(
                    target=arg_name.deep_clone(),
                    iter=items.deep_clone(),
                    ifs=[cst.CompIf(test=predicate.body.deep_clone())],
                ),
            )
            self.record_hit(
                hit_at(
                    rule_id="filter-lambda-to-generator",
                    message="Replace filtering with a lambda with a generator expression",
                    path=self.path,
                    node=node,
                    before=code_span(node),
                    after=code_span(after),
                ),
                node,
            )
            return True


class NoComplexIfExpressionsRule:
    rule_id = "no-complex-if-expressions"
    kind = RuleKind.SUGGESTION
    summary = "Only use conditional expressions for simple cases"
    apply_mode = ApplyMode.HINT

    def detect(self, source: str, path: str) -> list[Hit]:
        _ = self
        return detect_with_visitor(source, path, NoComplexIfExpressionsRule.Finder)

    def apply(self, source: str, hits: Sequence[Hit]) -> str | None:
        _ = self
        return noop_apply(source, hits)

    class Finder(HitCollector):
        def visit_IfExp(self, node: cst.IfExp) -> bool:  # ruff:ignore[invalid-function-name]
            arms = (code_span(node.body), code_span(node.test), code_span(node.orelse))
            if all(len(arm) <= IF_EXP_ARM_LIMIT for arm in arms):
                return True
            self.record_hit(
                hit_at(
                    rule_id="no-complex-if-expressions",
                    message="Only use conditional expressions for simple cases",
                    path=self.path,
                    node=node,
                ),
                node,
            )
            return True
