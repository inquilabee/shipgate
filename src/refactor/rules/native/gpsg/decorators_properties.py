"""GPSG native: do-not-use-staticmethod, avoid-trivial-properties."""

from __future__ import annotations

from typing import TYPE_CHECKING

import libcst as cst

from refactor.call_match import decorator_names
from refactor.cst_util import HitCollector, detect_with_visitor, noop_apply
from refactor.protocol import ApplyMode, RuleKind
from refactor.rules.native.gpsg.helpers import code_span, hit_at

if TYPE_CHECKING:
    from collections.abc import Sequence

    from refactor.protocol import Hit


class DoNotUseStaticmethodRule:
    rule_id = "do-not-use-staticmethod"
    kind = RuleKind.SUGGESTION
    summary = "Do not use the staticmethod decorator"
    apply_mode = ApplyMode.HINT

    def detect(self, source: str, path: str) -> list[Hit]:
        _ = self
        return detect_with_visitor(source, path, DoNotUseStaticmethodRule.Finder)

    def apply(self, source: str, hits: Sequence[Hit]) -> str | None:
        _ = self
        return noop_apply(source, hits)

    class Finder(HitCollector):
        def visit_FunctionDef(  # ruff:ignore[invalid-function-name]
            self,
            node: cst.FunctionDef,
        ) -> bool:
            names = decorator_names(node.decorators)
            if names != {"staticmethod"}:
                return True
            self.record_hit(
                hit_at(
                    rule_id="do-not-use-staticmethod",
                    message="Do not use the staticmethod decorator",
                    path=self.path,
                    node=node,
                ),
                node,
            )
            return True


class AvoidTrivialPropertiesRule:
    rule_id = "avoid-trivial-properties"
    kind = RuleKind.SUGGESTION
    summary = "Avoid defining trivial properties"
    apply_mode = ApplyMode.HINT

    def detect(self, source: str, path: str) -> list[Hit]:
        _ = self
        return detect_with_visitor(source, path, AvoidTrivialPropertiesRule.Finder)

    def apply(self, source: str, hits: Sequence[Hit]) -> str | None:
        _ = self
        return noop_apply(source, hits)

    class Finder(HitCollector):
        def visit_ClassDef(self, node: cst.ClassDef) -> bool:  # ruff:ignore[invalid-function-name]
            methods = [item for item in node.body.body if isinstance(item, cst.FunctionDef)]
            getters = {
                item.name.value: item
                for item in methods
                if "property" in decorator_names(item.decorators)
            }
            for name, getter in getters.items():
                attr = self.trivial_property_attr(getter)
                if attr is None:
                    continue
                setter = self.find_setter(methods, name)
                if setter is None or not self.trivial_setter_writes(setter, attr):
                    continue
                self.record_hit(
                    hit_at(
                        rule_id="avoid-trivial-properties",
                        message="Avoid defining trivial properties",
                        path=self.path,
                        node=getter,
                        before=code_span(getter),
                    ),
                    getter,
                )
            return True

        @staticmethod
        def trivial_property_attr(node: cst.FunctionDef) -> str | None:
            body = node.body.body
            if len(body) != 1 or not isinstance(body[0], cst.SimpleStatementLine):
                return None
            stmt = body[0].body
            if len(stmt) != 1 or not isinstance(stmt[0], cst.Return):
                return None
            value = stmt[0].value
            if not isinstance(value, cst.Attribute) or not isinstance(value.value, cst.Name):
                return None
            if value.value.value != "self":
                return None
            return value.attr.value

        @staticmethod
        def find_setter(
            methods: Sequence[cst.FunctionDef],
            name: str,
        ) -> cst.FunctionDef | None:
            for method in methods:
                setter = AvoidTrivialPropertiesRule.Finder.setter_for_name(method, name)
                if setter is not None:
                    return setter
            return None

        @staticmethod
        def setter_for_name(method: cst.FunctionDef, name: str) -> cst.FunctionDef | None:
            for decorator in method.decorators:
                deco = decorator.decorator
                if (
                    isinstance(deco, cst.Attribute)
                    and isinstance(deco.value, cst.Name)
                    and deco.value.value == name
                    and deco.attr.value == "setter"
                ):
                    return method
            return None

        @staticmethod
        def trivial_setter_writes(node: cst.FunctionDef, attr: str) -> bool:
            params = [param.name.value for param in node.params.params]
            if len(params) < 2 or params[0] != "self":
                return False
            value_name = params[1]
            body = node.body.body
            if len(body) != 1 or not isinstance(body[0], cst.SimpleStatementLine):
                return False
            stmt = body[0].body
            if len(stmt) != 1 or not isinstance(stmt[0], cst.Assign):
                return False
            assign = stmt[0]
            if len(assign.targets) != 1:
                return False
            target = assign.targets[0].target
            return (
                False
                if not isinstance(target, cst.Attribute) or not isinstance(target.value, cst.Name)
                else (
                    False
                    if target.value.value != "self" or target.attr.value != attr
                    else (isinstance(assign.value, cst.Name) and assign.value.value == value_name)
                )
            )
