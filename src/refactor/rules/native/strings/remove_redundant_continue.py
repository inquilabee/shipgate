"""Native rule for ``remove-redundant-continue``."""

from __future__ import annotations

from typing import TYPE_CHECKING

import libcst as cst
from libcst.metadata import ParentNodeProvider, PositionProvider

from refactor.cst_util import HitCollector, body_cleanup_hit
from refactor.rules.native.expr_base import BodyCleanupRule

if TYPE_CHECKING:
    from collections.abc import Sequence

    from refactor.cst_util import BodyStatement


class RemoveRedundantContinueRule(BodyCleanupRule):
    rule_id = "remove-redundant-continue"
    summary = "Remove redundant continue"
    message = "Remove a redundant trailing continue"

    @classmethod
    def match_body(
        cls,
        body: Sequence[cst.BaseStatement],
    ) -> tuple[cst.BaseStatement, Sequence[BodyStatement]] | None:
        return (
            None
            if not body or not cls.is_continue_stmt(body[-1])
            else (
                body[-1],
                list(body[:-1]),
            )
        )

    @staticmethod
    def is_continue_stmt(stmt: cst.BaseStatement) -> bool:
        return (
            isinstance(stmt, cst.SimpleStatementLine)
            and len(stmt.body) == 1
            and isinstance(stmt.body[0], cst.Continue)
        )

    @staticmethod
    def loop_body(
        block: cst.IndentedBlock,
        parent: cst.CSTNode | None,
    ) -> bool:
        _ = block
        return isinstance(parent, (cst.For, cst.While))

    @classmethod
    def finder_type(cls) -> type[HitCollector]:
        rule = cls

        class Finder(HitCollector):
            METADATA_DEPENDENCIES = (PositionProvider, ParentNodeProvider)

            def visit_IndentedBlock(
                self,
                node: cst.IndentedBlock,
            ) -> bool:
                parent = self.get_metadata(ParentNodeProvider, node)
                if not rule.loop_body(node, parent):
                    return True
                match = rule.match_body(node.body)
                if match is None:
                    return True
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
                return True

        Finder.__name__ = f"{cls.__name__}Finder"
        Finder.__qualname__ = Finder.__name__
        return Finder
