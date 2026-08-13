"""Parallel suite execution."""

from __future__ import annotations

from concurrent.futures import Future, ThreadPoolExecutor, as_completed
from typing import TYPE_CHECKING, TypeVar

if TYPE_CHECKING:
    from collections.abc import Callable

T = TypeVar("T")
R = TypeVar("R")


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
    futures: dict[Future[R], int],
    results: dict[int, R],
    *,
    fail_fast: bool,
) -> None:
    errors: list[BaseException] = []

    def attach_finished(exc: BaseException) -> None:
        attach = getattr(exc, "attach_completed", None)
        if callable(attach):
            attach([results[i] for i in sorted(results)])

    for future in as_completed(futures):
        index = futures[future]
        try:
            results[index] = future.result()
        except BaseException as exc:
            errors.append(exc)
            if fail_fast:
                for pending in futures:
                    pending.cancel()
                attach_finished(exc)
                raise
    if errors:
        attach_finished(errors[0])
        raise errors[0]
