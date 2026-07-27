"""Path/block scoring helpers shared by radon normalize and calibrate."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence


@dataclass(frozen=True)
class ScoredMetric:
    """One scored radon unit (file for MI, block for CC)."""

    path: str
    score: float
    detail: str | None = None
    line: int | None = None


class RadonScores:
    """Extract and rank scored MI/CC units from radon JSON payloads."""

    DEFAULT_OFFENDER_LIMIT: int = 15

    @classmethod
    def mi_items(cls, payload: Mapping[str, object]) -> list[ScoredMetric]:
        items: list[ScoredMetric] = []
        for file_path, item in payload.items():
            if not isinstance(item, dict):
                continue
            mi_value = item.get("mi")
            if isinstance(mi_value, (int, float)):
                items.append(ScoredMetric(path=str(file_path), score=float(mi_value)))
        return items

    @classmethod
    def cc_items(cls, payload: Mapping[str, object]) -> list[ScoredMetric]:
        items: list[ScoredMetric] = []
        for file_path, blocks in payload.items():
            if not isinstance(blocks, list):
                continue
            for block in blocks:
                if not isinstance(block, dict):
                    continue
                complexity = block.get("complexity")
                if not isinstance(complexity, (int, float)):
                    continue
                block_type = str(block.get("type", "block"))
                name = str(block.get("name", ""))
                detail = f"{block_type} {name}".strip()
                lineno = block.get("lineno")
                items.append(
                    ScoredMetric(
                        path=str(file_path),
                        score=float(complexity),
                        detail=detail or None,
                        line=lineno if isinstance(lineno, int) else None,
                    )
                )
        return items

    @classmethod
    def ranked_offenders(
        cls,
        items: Sequence[ScoredMetric],
        *,
        worse_when: str,
        limit: int = DEFAULT_OFFENDER_LIMIT,
    ) -> list[ScoredMetric]:
        if limit <= 0 or not items:
            return []
        reverse = worse_when == "higher"
        ordered = sorted(items, key=lambda item: item.score, reverse=reverse)
        return list(ordered[:limit])
