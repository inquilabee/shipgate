"""Parallel suite execution."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import TYPE_CHECKING, TypeVar

if TYPE_CHECKING:
    from collections.abc import Callable, Iterable

T = TypeVar("T")
R = TypeVar("R")


def run_sequential(items: Iterable[T], fn: Callable[[T], R]) -> list[R]:
    return [fn(item) for item in items]


def run_parallel(
    items: list[T],
    fn: Callable[[T], R],
    *,
    fail_fast: bool = False,
) -> list[R]:
    if not items:
        return []
    if len(items) == 1:
        return [fn(items[0])]

    results: dict[int, R] = {}
    with ThreadPoolExecutor(max_workers=min(len(items), 8)) as pool:
        futures = {pool.submit(fn, item): index for index, item in enumerate(items)}
        collect_parallel_results(futures, results, fail_fast=fail_fast)
    return [results[i] for i in range(len(items))]


def collect_parallel_results(
    futures: dict,
    results: dict[int, R],
    *,
    fail_fast: bool,
) -> None:
    failed = False
    for future in as_completed(futures):
        index = futures[future]
        try:
            results[index] = future.result()
        except Exception:
            failed = True
            if fail_fast:
                for pending in futures:
                    pending.cancel()
                raise
        if fail_fast and failed:
            break
