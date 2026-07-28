"""Native rule for ``switch``."""

from __future__ import annotations

import libcst as cst

from refactor.rules.native.stmt_base import IfRewriteRule


class SwitchRule(IfRewriteRule):
    rule_id = "switch"
    summary = "Switch"
    message = "Use match for repeated equality branches"

    @classmethod
    def match_stmt(cls, node: cst.CSTNode) -> cst.BaseStatement | None:
        if not isinstance(node, cst.If):
            return None
        subject, cases, default_body = cls.case_chain(node)
        if subject is None or len(cases) < 2:
            return None
        match_cases = [
            cst.MatchCase(
                pattern=cst.MatchValue(value=value),
                body=body,
            )
            for value, body in cases
        ]
        if default_body is not None:
            match_cases.append(cst.MatchCase(pattern=cst.MatchAs(), body=default_body))
        return cst.Match(subject=subject, cases=match_cases)

    @classmethod
    def case_chain(
        cls,
        node: cst.If,
    ) -> tuple[
        cst.BaseExpression | None,
        list[tuple[cst.BaseExpression, cst.IndentedBlock]],
        cst.IndentedBlock | None,
    ]:
        subject: cst.BaseExpression | None = None
        cases: list[tuple[cst.BaseExpression, cst.IndentedBlock]] = []
        current: cst.If | None = node
        default_body: cst.IndentedBlock | None = None
        while current is not None:
            branch_subject, value = cls.equality_case(current.test)
            if branch_subject is None or value is None:
                return None, [], None
            if subject is None:
                subject = branch_subject
            elif not subject.deep_equals(branch_subject):
                return None, [], None
            if not isinstance(current.body, cst.IndentedBlock):
                return None, [], None
            cases.append((value, current.body))
            next_branch = cls.next_branch(current.orelse)
            if next_branch is not None:
                current = next_branch
                continue
            default_body = cls.default_body(current.orelse)
            if current.orelse is not None and default_body is None:
                return None, [], None
            current = None
        return subject, cases, default_body

    @staticmethod
    def next_branch(orelse: cst.If | cst.Else | None) -> cst.If | None:
        return orelse if isinstance(orelse, cst.If) else None

    @staticmethod
    def default_body(orelse: cst.If | cst.Else | None) -> cst.IndentedBlock | None:
        return (
            (orelse.body if isinstance(orelse.body, cst.IndentedBlock) else None)
            if isinstance(orelse, cst.Else)
            else None
        )

    @staticmethod
    def equality_case(
        test: cst.BaseExpression,
    ) -> tuple[cst.BaseExpression | None, cst.BaseExpression | None]:
        if not isinstance(test, cst.Comparison) or len(test.comparisons) != 1:
            return None, None
        target = test.comparisons[0]
        return (
            (test.left, target.comparator)
            if isinstance(target.operator, cst.Equal)
            else (None, None)
        )
