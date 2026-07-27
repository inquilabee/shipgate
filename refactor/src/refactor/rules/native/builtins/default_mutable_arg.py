"""Flag mutable default arguments and suggest ``None`` sentinel pattern."""

from __future__ import annotations

from typing import TYPE_CHECKING, cast

import libcst as cst

from refactor.protocol import Hit, Location, RuleKind, Suggestion

if TYPE_CHECKING:
    from collections.abc import Sequence


class DefaultMutableArgRule:
    rule_id = "default-mutable-arg"
    kind = RuleKind.SUGGESTION
    summary = "Avoid mutable default arguments; use `None` and initialize in body"
    safe_apply = False

    def detect(self, source: str, path: str) -> list[Hit]:
        _ = self
        module = cst.parse_module(source)
        finder = DefaultMutableArgRule.Finder(path=path)
        module.visit(finder)
        return finder.hits

    def apply(self, source: str, hits: Sequence[Hit]) -> str | None:
        _ = self, source, hits
        return None

    class Finder(cst.CSTVisitor):
        def __init__(self, *, path: str) -> None:
            self.path = path
            self.hits: list[Hit] = []

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
        before = cst.Module(body=[func]).code.strip()
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
            body=[init_stmt, *cast("Sequence[cst.BaseStatement]", func.body.body)]
        )
        after_func = func.with_changes(
            params=func.params.with_changes(params=new_params),
            body=new_body,
        )
        after = cst.Module(body=[after_func]).code.strip()
        hint = f"Use `None` default and `if {param_name} is None: {param_name} = {default_kind}()`"
        return Hit(
            rule_id="default-mutable-arg",
            message=f"Avoid mutable default for `{param_name}`",
            location=Location(path=path),
            suggestion=Suggestion(before=before, after=after, message=hint),
        )

    @staticmethod
    def mutable_kind(node: cst.BaseExpression) -> str:
        if isinstance(node, cst.List):
            return "list"
        if isinstance(node, cst.Dict):
            return "dict"
        return "set"

    @staticmethod
    def empty_mutable(kind: str) -> cst.BaseExpression:
        if kind == "list":
            return cst.List(elements=[])
        if kind == "dict":
            return cst.Dict(elements=[])
        return cst.Set(elements=[])
