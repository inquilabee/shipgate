"""Apply suggest-only refactor rules via libcst transforms."""

from __future__ import annotations

from typing import TYPE_CHECKING, cast

import libcst as cst
from libcst.metadata import MetadataWrapper, ParentNodeProvider

from refactor.detector import (
    RuleT,
    custom_detect_rules,
    has_base_finder,
)
from refactor.rules.native.assign.collection_to_bool import CollectionToBoolRule
from refactor.rules.native.builtins.identity_comprehension import (
    IdentityComprehensionRule,
)
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
from refactor.rules.native.strings.remove_redundant_continue import (
    RemoveRedundantContinueRule,
)

if TYPE_CHECKING:
    from collections.abc import Sequence
    from pathlib import Path

    from refactor.protocol import RefactorRule


SAFE_SUGGEST_RULE_IDS = frozenset(
    {
        "collection-to-bool",
        "remove-unnecessary-cast",
        "remove-redundant-boolean",
        "dict-assign-update-to-union",
        "simplify-dictionary-update",
        "remove-redundant-exception",
        "or-if-exp-identity",
        "use-or-for-fallback",
        "use-getitem-for-re-match-groups",
        "ternary-to-if-expression",
        "chain-compares",
        "merge-comparisons",
        "invert-any-all",
        "convert-any-to-in",
    }
)

STMT_SUGGEST_RULE_IDS = frozenset(
    {
        "introduce-default-else",
        "use-named-expression",
        "merge-dict-assign",
        "remove-dict-keys",
        "use-itertools-product",
        "instance-method-first-arg-name",
        "swap-if-else-branches",
        "swap-if-expression",
        "use-contextlib-suppress",
        "remove-pass-body",
        "merge-list-append",
        "merge-list-appends-into-extend",
        "inline-variable",
        "use-assigned-variable",
        "inline-immediately-returned-variable",
        "use-string-remove-affix",
        "guard",
        "identity-comprehension",
        "extract-duplicate-method",
        "switch",
        "use-or-for-fallback",
        "or-if-exp-identity",
        "invert-any-all",
        "invert-any-all-body",
        "hoist-if-from-if",
        "swap-nested-ifs",
        "merge-repeated-ifs",
        "hoist-repeated-if-condition",
        "hoist-loop-from-if",
        "use-join",
        "while-to-for",
        "chain-compares",
        "merge-comparisons",
        "convert-any-to-in",
        "collection-to-bool",
        "assign-if-exp",
        "raise-from-previous-error",
        "remove-redundant-continue",
    }
)


def apply_suggest_paths(
    paths: Sequence[Path],
    *,
    rules: Sequence[RefactorRule] | None = None,
    rule_ids: frozenset[str] | None = SAFE_SUGGEST_RULE_IDS,
) -> list[Path]:
    from refactor.runner import check_rules, iter_python_files

    if rule_ids is not None:
        all_rules = check_rules(rules)
        selected = tuple(rule for rule in all_rules if rule.rule_id in rule_ids)
    else:
        selected = check_rules(rules)
    changed: list[Path] = []
    for file_path in iter_python_files(paths):
        source = file_path.read_text(encoding="utf-8")
        rewritten = apply_suggest_source(source, str(file_path), selected)
        if rewritten != source:
            file_path.write_text(rewritten, encoding="utf-8")
            changed.append(file_path)
    return changed


def apply_suggest_source(
    source: str,
    path: str,
    rules: Sequence[RefactorRule],
) -> str:
    for _ in range(100):
        updated = apply_suggest_once(source, path, rules)
        if updated == source:
            return source
        source = updated
    return source


def apply_suggest_once(
    source: str,
    path: str,
    rules: Sequence[RefactorRule],
) -> str:
    module = cst.parse_module(source)
    wrapper = MetadataWrapper(module)
    transformer = CombinedSuggestTransformer(path=path, rules=rules)
    updated = wrapper.visit(transformer)
    rewritten = updated.code
    if rewritten != source:
        return rewritten
    for rule in custom_detect_rules(rules):
        if rule.safe_apply:
            continue
        hits = rule.detect(source, path)
        if not hits:
            continue
        applied = rule.apply(source, hits)
        if applied is not None and applied != source:
            return applied
    return source


class CombinedSuggestTransformer(cst.CSTTransformer, cst.MetadataDependent):
    METADATA_DEPENDENCIES = (ParentNodeProvider,)

    def __init__(self, *, path: str, rules: Sequence[RefactorRule]) -> None:
        self.path = path
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
        self.call_rules = (
            *self.call_rules,
            *tuple(rule for rule in rules if isinstance(rule, CollectionToBoolRule)),
        )

    def leave_Call(  # ruff:ignore[invalid-function-name]
        self,
        original_node: cst.Call,
        updated_node: cst.Call,
    ) -> cst.BaseExpression:
        _ = original_node
        return self.apply_expr_rules(updated_node, self.call_rules)

    def leave_BinaryOperation(  # ruff:ignore[invalid-function-name]
        self,
        original_node: cst.BinaryOperation,
        updated_node: cst.BinaryOperation,
    ) -> cst.BaseExpression:
        _ = original_node
        return self.apply_expr_rules(updated_node, self.binary_op_rules)

    def leave_BooleanOperation(  # ruff:ignore[invalid-function-name]
        self,
        original_node: cst.BooleanOperation,
        updated_node: cst.BooleanOperation,
    ) -> cst.BaseExpression:
        _ = original_node
        return self.apply_expr_rules(updated_node, self.boolean_op_rules)

    def leave_UnaryOperation(  # ruff:ignore[invalid-function-name]
        self,
        original_node: cst.UnaryOperation,
        updated_node: cst.UnaryOperation,
    ) -> cst.BaseExpression:
        _ = original_node
        return self.apply_expr_rules(updated_node, self.unary_op_rules)

    def leave_IfExp(  # ruff:ignore[invalid-function-name]
        self,
        original_node: cst.IfExp,
        updated_node: cst.IfExp,
    ) -> cst.BaseExpression:
        _ = original_node
        return self.apply_expr_rules(updated_node, self.if_exp_rules)

    def leave_Comparison(  # ruff:ignore[invalid-function-name]
        self,
        original_node: cst.Comparison,
        updated_node: cst.Comparison,
    ) -> cst.BaseExpression:
        _ = original_node
        return self.apply_expr_rules(updated_node, self.comparison_rules)

    def leave_Dict(  # ruff:ignore[invalid-function-name]
        self,
        original_node: cst.Dict,
        updated_node: cst.Dict,
    ) -> cst.BaseExpression:
        _ = original_node
        return self.apply_expr_rules(updated_node, self.dict_rules)

    def leave_Set(  # ruff:ignore[invalid-function-name]
        self,
        original_node: cst.Set,
        updated_node: cst.Set,
    ) -> cst.BaseExpression:
        _ = original_node
        return self.apply_expr_rules(updated_node, self.set_rules)

    def leave_Subscript(  # ruff:ignore[invalid-function-name]
        self,
        original_node: cst.Subscript,
        updated_node: cst.Subscript,
    ) -> cst.BaseExpression:
        _ = original_node
        return self.apply_expr_rules(updated_node, self.subscript_rules)

    def leave_FormattedString(  # ruff:ignore[invalid-function-name]
        self,
        original_node: cst.FormattedString,
        updated_node: cst.FormattedString,
    ) -> cst.BaseExpression:
        _ = original_node
        return self.apply_expr_rules(updated_node, self.formatted_string_rules)

    def leave_ListComp(  # ruff:ignore[invalid-function-name,no-self-use]
        self,
        original_node: cst.ListComp,
        updated_node: cst.ListComp,
    ) -> cst.BaseExpression:
        _ = original_node
        replacement = IdentityComprehensionRule.match_identity(updated_node)
        return (
            updated_node
            if replacement is None
            else cst.Call(func=cst.Name("list"), args=[cst.Arg(value=replacement)])
        )

    def leave_If(  # ruff:ignore[invalid-function-name]
        self,
        original_node: cst.If,
        updated_node: cst.If,
    ) -> cst.BaseStatement:
        _ = original_node
        return self.apply_stmt_rules(updated_node, self.if_rules)

    def leave_For(  # ruff:ignore[invalid-function-name]
        self,
        original_node: cst.For,
        updated_node: cst.For,
    ) -> cst.BaseStatement:
        _ = original_node
        return self.apply_stmt_rules(updated_node, self.for_rules)

    def leave_While(  # ruff:ignore[invalid-function-name]
        self,
        original_node: cst.While,
        updated_node: cst.While,
    ) -> cst.BaseStatement:
        _ = original_node
        return self.apply_stmt_rules(updated_node, self.while_rules)

    def leave_Try(  # ruff:ignore[invalid-function-name]
        self,
        original_node: cst.Try,
        updated_node: cst.Try,
    ) -> cst.BaseStatement:
        _ = original_node
        return self.apply_stmt_rules(updated_node, self.try_rules)

    def leave_FunctionDef(  # ruff:ignore[invalid-function-name]
        self,
        original_node: cst.FunctionDef,
        updated_node: cst.FunctionDef,
    ) -> cst.BaseStatement:
        _ = original_node
        return self.apply_stmt_rules(updated_node, self.function_rules)

    def leave_SimpleStatementLine(  # ruff:ignore[invalid-function-name]
        self,
        original_node: cst.SimpleStatementLine,
        updated_node: cst.SimpleStatementLine,
    ) -> cst.BaseStatement:
        _ = original_node
        return self.apply_stmt_rules(updated_node, self.simple_statement_line_rules)

    def leave_Module(  # ruff:ignore[invalid-function-name]
        self,
        original_node: cst.Module,
        updated_node: cst.Module,
    ) -> cst.Module:
        _ = original_node
        body = self.apply_body_rules(updated_node.body)
        return updated_node if body is updated_node.body else updated_node.with_changes(body=body)

    def leave_IndentedBlock(  # ruff:ignore[invalid-function-name]
        self,
        original_node: cst.IndentedBlock,
        updated_node: cst.IndentedBlock,
    ) -> cst.IndentedBlock:
        _ = original_node
        body = self.apply_body_rules(updated_node.body)
        body = self.apply_loop_continue_cleanup(updated_node, body)
        return updated_node if body is updated_node.body else updated_node.with_changes(body=body)

    def apply_loop_continue_cleanup(
        self,
        block: cst.IndentedBlock,
        body: Sequence[cst.BaseStatement],
    ) -> Sequence[cst.BaseStatement]:
        parent = self.parent_of(block)
        if not RemoveRedundantContinueRule.loop_body(block, parent):
            return body
        match = RemoveRedundantContinueRule.match_body(body)
        if match is None:
            return body
        _, cleaned = match
        return cleaned

    def apply_expr_rules(
        self,
        node: cst.BaseExpression,
        rules: Sequence[SuggestOnlyExprRule],
    ) -> cst.BaseExpression:
        expression = node
        for rule in rules:
            replacement = rule.match(node)
            if replacement is None:
                continue
            if isinstance(node, cst.Call) and isinstance(rule, CollectionToBoolRule):
                parent = self.parent_of(node)
                if not CollectionToBoolRule.truthiness_len(node, parent):
                    continue
            return replacement
        return expression

    @staticmethod
    def apply_stmt_rules(
        node: cst.BaseStatement,
        rules: Sequence[StatementRewriteRule],
    ) -> cst.BaseStatement:
        statement = node
        for rule in rules:
            replacement = rule.match_stmt(node)
            if replacement is None or not isinstance(replacement, cst.BaseStatement):
                continue
            return replacement
        return statement

    def apply_body_rules(
        self,
        body: Sequence[cst.BaseStatement],
    ) -> Sequence[cst.BaseStatement]:
        current = list(body)
        for rule in self.body_cleanup_rules:
            match = rule.match_body(current)
            if match is not None:
                _, cleaned = match
                return cleaned
        for rule in self.body_sequence_rules:
            match = rule.match_body(current)
            if match is None:
                continue
            before, after = match
            if not before:
                continue
            index = self.subsequence_index(current, before)
            if index < 0:
                continue
            return [
                *current[:index],
                *after,
                *current[index + len(before) :],
            ]
        expanded = self.expand_if_statement_bodies(current, self.if_rules)
        return expanded if expanded is not current else current

    def parent_of(self, node: cst.CSTNode) -> cst.CSTNode | None:
        try:
            return self.get_metadata(ParentNodeProvider, node)
        except KeyError:
            return None

    @staticmethod
    def rules_for_base(
        rules: Sequence[RefactorRule],
        base: type[RuleT],
    ) -> tuple[RuleT, ...]:
        return tuple(cast("RuleT", rule) for rule in rules if has_base_finder(rule, base))

    @staticmethod
    def expand_if_statement_bodies(
        body: Sequence[cst.BaseStatement],
        if_rules: Sequence[IfRewriteRule],
    ) -> list[cst.BaseStatement]:
        expanded: list[cst.BaseStatement] = []
        changed = False
        for stmt in body:
            if not isinstance(stmt, cst.If):
                expanded.append(stmt)
                continue
            replacement: cst.BaseStatement | Sequence[cst.BaseStatement] | None = None
            for rule in if_rules:
                match = rule.match_stmt(stmt)
                if match is not None and not isinstance(match, cst.BaseStatement):
                    replacement = match
                    break
            if replacement is None:
                expanded.append(stmt)
                continue
            changed = True
            expanded.extend(replacement)
        return expanded if changed else list(body)

    @staticmethod
    def subsequence_index(
        body: Sequence[cst.BaseStatement],
        target: Sequence[cst.BaseStatement],
    ) -> int:
        target_list = list(target)
        if not target_list:
            return -1
        for index in range(len(body) - len(target_list) + 1):
            if all(
                body[index + offset] is target_list[offset] for offset in range(len(target_list))
            ):
                return index
        return -1
