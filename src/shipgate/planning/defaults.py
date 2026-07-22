"""Default option resolution."""

from pathlib import Path

from shipgate.domain.modes import RunMode
from shipgate.domain.options import NormalizedOptions
from shipgate.planning.option_resolver import OptionResolver


def apply_defaults(
    options: NormalizedOptions,
    *,
    mode: RunMode,
    check_id: str,
    project_root: Path,
    target: Path,
    sources: dict[str, str],
) -> tuple[NormalizedOptions, dict[str, str]]:
    return OptionResolver().apply_defaults(
        options,
        mode=mode,
        check_id=check_id,
        project_root=project_root,
        target=target,
        sources=sources,
    )
