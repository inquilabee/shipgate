"""Flag mutable default arguments and suggest ``None`` sentinel pattern."""

from __future__ import annotations

from typing import TYPE_CHECKING, cast

import libcst as cst

from refactor.cst_util import (
    HitCollector,
    code_for_stmt,
    detect_with_visitor,
    make_hit,
    noop_apply,
)
from refactor.protocol import ApplyMode, RuleKind

if TYPE_CHECKING:
    from collections.abc import Sequence

    from refactor.protocol import Hit


class DefaultMutableArgRule:
    rule_id = "default-mutable-arg"
    kind = RuleKind.SUGGESTION
    summary = "Avoid mutable default arguments; use `None` and initialize in body"
    apply_mode = ApplyMode.HINT

    def detect(self, source: str, path: str) -> list[Hit]:
        _ = self
        return detect_with_visitor(source, path, DefaultMutableArgRule.Finder)

    def apply(self, source: str, hits: Sequence[Hit]) -> str | None:
        _ = self
        return noop_apply(source, hits)

    class Finder(HitCollector):
        def visit_FunctionDef(  # ruff:ignore[invalid-function-name]
            self,
            node: cst.FunctionDef,
        ) -> bool:
            for param in node.params.params:
                if param.default is None:
                    continue
                if not DefaultMutableArgRule.is_mutable_default(param.default):
                    continue
                self.hits.append(DefaultMutableArgRule.hit_for(node, param, self.path))
            return True

    @staticmethod
    def is_mutable_default(node: cst.BaseExpression) -> bool:
        return isinstance(node, (cst.List, cst.Dict, cst.Set))

    @staticmethod
    def hit_for(
        func: cst.FunctionDef,
        param: cst.Param,
        path: str,
    ) -> Hit:
        param_name = param.name.value
        default_expr = param.default
        if default_expr is None:
            raise ValueError("mutable default parameter missing default expression")
        default_kind = DefaultMutableArgRule.mutable_kind(default_expr)
        new_params = []
        for existing in func.params.params:
            if existing is param:
                new_params.append(existing.with_changes(default=cst.Name("None")))
            else:
                new_params.append(existing)
        init_stmt = cst.If(
            test=cst.Comparison(
                left=cst.Name(param_name),
                comparisons=[
                    cst.ComparisonTarget(
                        operator=cst.Is(),
                        comparator=cst.Name("None"),
                    )
                ],
            ),
            body=cst.IndentedBlock(
                body=[
                    cst.SimpleStatementLine(
                        body=[
                            cst.Assign(
                                targets=[cst.AssignTarget(target=cst.Name(param_name))],
                                value=DefaultMutableArgRule.empty_mutable(default_kind),
                            )
                        ]
                    )
                ]
            ),
        )
        new_body = cst.IndentedBlock(
            body=cast("list[cst.BaseStatement]", [init_stmt, *func.body.body]),
        )
        after_func = func.with_changes(
            params=func.params.with_changes(params=new_params),
            body=new_body,
        )
        hint = f"Use `None` default and `if {param_name} is None: {param_name} = {default_kind}()`"
        return make_hit(
            rule_id="default-mutable-arg",
            message=f"Avoid mutable default for `{param_name}`",
            path=path,
            before=code_for_stmt(func),
            after=code_for_stmt(after_func),
            suggestion_message=hint,
        )

    @staticmethod
    def mutable_kind(node: cst.BaseExpression) -> str:
        return (
            "list"
            if isinstance(node, cst.List)
            else ("dict" if isinstance(node, cst.Dict) else "set")
        )

    @staticmethod
    def empty_mutable(kind: str) -> cst.BaseExpression:
        return (
            cst.List(elements=[])
            if kind == "list"
            else (cst.Dict(elements=[]) if kind == "dict" else cst.Set(elements=[]))
        )
