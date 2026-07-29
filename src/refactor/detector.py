"""Detection engine for running registered refactor rules over one source file."""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol, TypeVar, cast

import libcst as cst
from libcst.metadata import MetadataWrapper

from refactor.cst_util import (
    HitCollector,
    body_cleanup_hit,
    parse_module_cached,
    stmts_replacement_hit,
)
from refactor.registry import RULES
from refactor.rules.native.expr_base import (
    BinaryOpRewriteRule,
    BodyCleanupRule,
    BooleanOpRewriteRule,
    CallRewriteRule,
    ComparisonRewriteRule,
    DictRewriteRule,
    FormattedStringRewriteRule,
    IfExpRewriteRule,
    SetRewriteRule,
    SubscriptRewriteRule,
    SuggestOnlyExprRule,
    UnaryOpRewriteRule,
)
from refactor.rules.native.stmt_base import (
    BodySequenceRewriteRule,
    ForRewriteRule,
    FunctionRewriteRule,
    IfRewriteRule,
    SimpleStatementLineRewriteRule,
    StatementRewriteRule,
    TryRewriteRule,
    WhileRewriteRule,
)

if TYPE_CHECKING:
    from collections.abc import Sequence

    from refactor.protocol import Hit, RefactorRule

RuleT = TypeVar("RuleT")


class StandardVisitorRule(Protocol):
    @classmethod
    def finder_type(cls) -> type[HitCollector]: ...


def detect_file(source: str, path: str, rules: Sequence[RefactorRule]) -> list[Hit]:
    hits: list[Hit] = []
    hits.extend(detect_combined_rules(source, path, rules))
    hits.extend(detect_standard_rules(source, path, rules))
    for rule in custom_detect_rules(rules):
        hits.extend(rule.detect(source, path))
    return hits


def detect_combined_rules(
    source: str,
    path: str,
    rules: Sequence[RefactorRule],
) -> list[Hit]:
    combined_rules = [
        rule
        for rule in rules
        if can_use_combined_visitor(rule) and uses_standard_visitor_detect(rule)
    ]
    if not combined_rules:
        return []
    module = parse_module_cached(source)
    collector = CombinedRuleCollector(path=path, rules=combined_rules)
    MetadataWrapper(module, unsafe_skip_copy=True).visit(collector)
    return collector.hits


def detect_standard_rules(
    source: str,
    path: str,
    rules: Sequence[RefactorRule],
) -> list[Hit]:
    standard_rules = [
        rule
        for rule in rules
        if uses_standard_visitor_detect(rule) and not can_use_combined_visitor(rule)
    ]
    if not standard_rules:
        return []
    module = parse_module_cached(source)
    wrapper = MetadataWrapper(module, unsafe_skip_copy=True)
    hits: list[Hit] = []
    for rule in standard_rules:
        finder_type = cast("StandardVisitorRule", rule).finder_type
        finder = finder_type()(path=path)
        wrapper.visit(finder)
        hits.extend(finder.hits)
    return hits


def custom_detect_rules(rules: Sequence[RefactorRule]) -> tuple[RefactorRule, ...]:
    return tuple(rule for rule in rules if not uses_standard_visitor_detect(rule))


class CombinedRuleCollector(HitCollector):
    def __init__(self, *, path: str, rules: Sequence[RefactorRule]) -> None:
        super().__init__(path=path)
        self.call_rules = self.rules_for_base(rules, CallRewriteRule)
        self.binary_op_rules = self.rules_for_base(rules, BinaryOpRewriteRule)
        self.boolean_op_rules = self.rules_for_base(rules, BooleanOpRewriteRule)
        self.unary_op_rules = self.rules_for_base(rules, UnaryOpRewriteRule)
        self.if_exp_rules = self.rules_for_base(rules, IfExpRewriteRule)
        self.comparison_rules = self.rules_for_base(rules, ComparisonRewriteRule)
        self.dict_rules = self.rules_for_base(rules, DictRewriteRule)
        self.set_rules = self.rules_for_base(rules, SetRewriteRule)
        self.subscript_rules = self.rules_for_base(rules, SubscriptRewriteRule)
        self.formatted_string_rules = self.rules_for_base(rules, FormattedStringRewriteRule)
        self.if_rules = self.rules_for_base(rules, IfRewriteRule)
        self.for_rules = self.rules_for_base(rules, ForRewriteRule)
        self.while_rules = self.rules_for_base(rules, WhileRewriteRule)
        self.try_rules = self.rules_for_base(rules, TryRewriteRule)
        self.function_rules = self.rules_for_base(rules, FunctionRewriteRule)
        self.simple_statement_line_rules = self.rules_for_base(
            rules,
            SimpleStatementLineRewriteRule,
        )
        self.body_sequence_rules = self.rules_for_base(rules, BodySequenceRewriteRule)
        self.body_cleanup_rules = self.rules_for_base(rules, BodyCleanupRule)

    def visit_Call(self, node: cst.Call) -> bool:
        self.record_expr_rules(node, self.call_rules)
        return True

    def visit_BinaryOperation(
        self,
        node: cst.BinaryOperation,
    ) -> bool:
        self.record_expr_rules(node, self.binary_op_rules)
        return True

    def visit_BooleanOperation(
        self,
        node: cst.BooleanOperation,
    ) -> bool:
        self.record_expr_rules(node, self.boolean_op_rules)
        return True

    def visit_UnaryOperation(
        self,
        node: cst.UnaryOperation,
    ) -> bool:
        self.record_expr_rules(node, self.unary_op_rules)
        return True

    def visit_IfExp(self, node: cst.IfExp) -> bool:
        self.record_expr_rules(node, self.if_exp_rules)
        return True

    def visit_Comparison(self, node: cst.Comparison) -> bool:
        self.record_expr_rules(node, self.comparison_rules)
        return True

    def visit_Dict(self, node: cst.Dict) -> bool:
        self.record_expr_rules(node, self.dict_rules)
        return True

    def visit_Set(self, node: cst.Set) -> bool:
        self.record_expr_rules(node, self.set_rules)
        return True

    def visit_Subscript(self, node: cst.Subscript) -> bool:
        self.record_expr_rules(node, self.subscript_rules)
        return True

    def visit_FormattedString(
        self,
        node: cst.FormattedString,
    ) -> bool:
        self.record_expr_rules(node, self.formatted_string_rules)
        return True

    def visit_If(self, node: cst.If) -> bool:
        self.record_stmt_rules(node, self.if_rules)
        return True

    def visit_For(self, node: cst.For) -> bool:
        self.record_stmt_rules(node, self.for_rules)
        return True

    def visit_While(self, node: cst.While) -> bool:
        self.record_stmt_rules(node, self.while_rules)
        return True

    def visit_Try(self, node: cst.Try) -> bool:
        self.record_stmt_rules(node, self.try_rules)
        return True

    def visit_FunctionDef(self, node: cst.FunctionDef) -> bool:
        self.record_stmt_rules(node, self.function_rules)
        return True

    def visit_SimpleStatementLine(
        self,
        node: cst.SimpleStatementLine,
    ) -> bool:
        self.record_stmt_rules(node, self.simple_statement_line_rules)
        return True

    def visit_Module(self, node: cst.Module) -> bool:
        self.record_body_rules(node.body)
        return True

    def visit_IndentedBlock(
        self,
        node: cst.IndentedBlock,
    ) -> bool:
        self.record_body_rules(node.body)
        return True

    def record_expr_rules(
        self,
        node: cst.CSTNode,
        rules: Sequence[SuggestOnlyExprRule],
    ) -> None:
        for rule in rules:
            replacement = rule.match(node)
            if replacement is not None:
                self.record_hit(rule.hit_for(node, replacement, self.path), node)

    def record_stmt_rules(
        self,
        node: cst.CSTNode,
        rules: Sequence[StatementRewriteRule],
    ) -> None:
        for rule in rules:
            replacement = rule.match_stmt(node)
            if replacement is not None:
                self.record_hit(rule.stmt_hit_for(node, replacement, self.path), node)

    def record_body_rules(self, body: Sequence[cst.BaseStatement]) -> None:
        for rule in self.body_sequence_rules:
            match = rule.match_body(body)
            if match is None:
                continue
            before, after = match
            if before:
                self.record_hit(
                    stmts_replacement_hit(
                        rule_id=rule.rule_id,
                        message=rule.message,
                        path=self.path,
                        before_stmts=before,
                        after_stmts=after,
                    ),
                    before[0],
                )
        for rule in self.body_cleanup_rules:
            match = rule.match_body(body)
            if match is None:
                continue
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

    @staticmethod
    def rules_for_base(
        rules: Sequence[RefactorRule],
        base: type[RuleT],
    ) -> tuple[RuleT, ...]:
        return tuple(cast("RuleT", rule) for rule in rules if has_base_finder(rule, base))


def uses_standard_visitor_detect(rule: RefactorRule) -> bool:
    return type(rule).detect is SuggestOnlyExprRule.detect


def can_use_combined_visitor(rule: RefactorRule) -> bool:
    return any(
        has_base_finder(rule, base)
        for base in (
            CallRewriteRule,
            BinaryOpRewriteRule,
            BooleanOpRewriteRule,
            UnaryOpRewriteRule,
            IfExpRewriteRule,
            ComparisonRewriteRule,
            DictRewriteRule,
            SetRewriteRule,
            SubscriptRewriteRule,
            FormattedStringRewriteRule,
            IfRewriteRule,
            ForRewriteRule,
            WhileRewriteRule,
            TryRewriteRule,
            FunctionRewriteRule,
            SimpleStatementLineRewriteRule,
            BodySequenceRewriteRule,
            BodyCleanupRule,
        )
    )


def has_base_finder(rule: RefactorRule, base: type[object]) -> bool:
    rule_finder_type = getattr(type(rule), "finder_type", None)
    if rule_finder_type is None:
        return False
    rule_finder = getattr(rule_finder_type, "__func__", None)
    base_finder_type = getattr(base, "finder_type", None)
    if base_finder_type is None:
        return False
    base_finder = getattr(base_finder_type, "__func__", None)
    return rule_finder is base_finder


def rule_enabled(rule: RefactorRule) -> bool:
    from refactor.protocol import ApplyMode

    mode = getattr(type(rule), "apply_mode", ApplyMode.HINT)
    return mode is not ApplyMode.OFF and getattr(type(rule), "enabled", True)


def check_rules(
    rules: Sequence[RefactorRule] | None = None,
    *,
    enable: frozenset[str] | None = None,
) -> tuple[RefactorRule, ...]:
    from refactor.inventory import inventory_by_id, rule_pack_selected

    # Explicit rule lists are caller-owned (tests/DI); pack gating applies to registry default.
    if rules is not None:
        return tuple(rules)
    selected = tuple(rule for rule in RULES if rule_enabled(rule))
    enable_tokens = frozenset() if enable is None else enable
    entries = inventory_by_id()
    return tuple(
        rule
        for rule in selected
        if rule_pack_selected(rule.rule_id, enable_tokens, inventory=entries)
    )
