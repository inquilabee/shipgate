"""GPSG native: type annotation requirements."""

from __future__ import annotations

from typing import TYPE_CHECKING

import libcst as cst

from refactor.cst_util import HitCollector, detect_with_visitor, noop_apply
from refactor.protocol import ApplyMode, RuleKind
from refactor.rules.native.gpsg.helpers import hit_at, is_test_path

if TYPE_CHECKING:
    from collections.abc import Sequence

    from refactor.protocol import Hit


class RequireParameterAnnotationRule:
    rule_id = "require-parameter-annotation"
    kind = RuleKind.SUGGESTION
    summary = "Annotate public function parameters with type annotations"
    apply_mode = ApplyMode.HINT

    def detect(self, source: str, path: str) -> list[Hit]:
        _ = self
        return (
            []
            if is_test_path(path)
            else detect_with_visitor(source, path, RequireParameterAnnotationRule.Finder)
        )

    def apply(self, source: str, hits: Sequence[Hit]) -> str | None:
        _ = self
        return noop_apply(source, hits)

    class Finder(HitCollector):
        def visit_FunctionDef(
            self,
            node: cst.FunctionDef,
        ) -> bool:
            if node.name.value.startswith("_"):
                return True
            for param in self.iter_params(node):
                name = param.name.value
                if name in {"self", "cls"} or param.annotation is not None:
                    continue
                self.record_hit(
                    hit_at(
                        rule_id="require-parameter-annotation",
                        message=(
                            f"Annotate parameter `{name}` in public function/method "
                            f"`{node.name.value}` with a type annotation"
                        ),
                        path=self.path,
                        node=param,
                    ),
                    param,
                )
            return True

        @staticmethod
        def iter_params(node: cst.FunctionDef) -> list[cst.Param]:
            params = node.params
            result: list[cst.Param] = [
                *params.params,
                *params.posonly_params,
                *params.kwonly_params,
            ]
            if isinstance(params.star_arg, cst.Param):
                result.append(params.star_arg)
            if isinstance(params.star_kwarg, cst.Param):
                result.append(params.star_kwarg)
            return result


class RequireReturnAnnotationRule:
    rule_id = "require-return-annotation"
    kind = RuleKind.SUGGESTION
    summary = "Annotate public functions with a return type annotation"
    apply_mode = ApplyMode.HINT

    def detect(self, source: str, path: str) -> list[Hit]:
        _ = self
        return (
            []
            if is_test_path(path)
            else detect_with_visitor(source, path, RequireReturnAnnotationRule.Finder)
        )

    def apply(self, source: str, hits: Sequence[Hit]) -> str | None:
        _ = self
        return noop_apply(source, hits)

    class Finder(HitCollector):
        def visit_FunctionDef(
            self,
            node: cst.FunctionDef,
        ) -> bool:
            if node.name.value.startswith("_") or node.returns is not None:
                return True
            self.record_hit(
                hit_at(
                    rule_id="require-return-annotation",
                    message=(
                        f"Annotate public function/method `{node.name.value}` "
                        "with a return type annotation"
                    ),
                    path=self.path,
                    node=node,
                ),
                node,
            )
            return True
