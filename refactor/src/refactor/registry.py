"""Explicit rule registry (no magic auto-discovery)."""

from __future__ import annotations

from typing import TYPE_CHECKING

from refactor.rules.bridge.ruff.list_literal import ListLiteralBridge
from refactor.rules.native.builtins.default_get import DefaultGetRule
from refactor.rules.native.builtins.min_max_identity import MinMaxIdentityRule
from refactor.rules.native.builtins.use_len import UseLenRule
from refactor.rules.native.syntax.aug_assign import AugAssignRule
from refactor.rules.native.syntax.dict_literal import DictLiteralRule
from refactor.rules.native.syntax.remove_redundant_pass import RemoveRedundantPassRule
from refactor.rules.native.syntax.tuple_literal import TupleLiteralRule

if TYPE_CHECKING:
    from refactor.protocol import RefactorRule

RULES: tuple[RefactorRule, ...] = (
    DefaultGetRule(),
    DictLiteralRule(),
    TupleLiteralRule(),
    RemoveRedundantPassRule(),
    UseLenRule(),
    MinMaxIdentityRule(),
    AugAssignRule(),
    ListLiteralBridge(),
)
