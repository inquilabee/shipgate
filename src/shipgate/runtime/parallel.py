"""Parallel suite execution."""

from __future__ import annotations

from concurrent.futures import Future, ThreadPoolExecutor, as_completed
from contextlib import suppress
from typing import TYPE_CHECKING, TypeVar

from shipgate.domain.reports import CheckReport

if TYPE_CHECKING:
    from collections.abc import Callable

T = TypeVar("T")
R = TypeVar("R")


class FailFastError(Exception):
    def __init__(self, report: CheckReport) -> None:
        super().__init__(report.check_id)
        self.report = report
        self.completed: list[CheckReport] = []

    def attach_completed(self, reports: list[CheckReport]) -> None:
        self.completed = list(reports)


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


def take_finished_results(
    futures: dict[Future[R], int],
    results: dict[int, R],
    *,
    skip: Future[R] | None = None,
) -> None:
    for future, index in futures.items():
        if future is skip or not future.done() or future.cancelled() or index in results:
            continue
        with suppress(Exception):
            results[index] = future.result()


def attach_fail_fast_completed(exc: BaseException, results: dict[int, R]) -> None:
    if not isinstance(exc, FailFastError):
        return
    reports: list[CheckReport] = []
    for index in sorted(results):
        report = results[index]
        if isinstance(report, CheckReport):
            reports.append(report)
    exc.attach_completed(reports)


def collect_parallel_results(
    futures: dict[Future[R], int],
    results: dict[int, R],
    *,
    fail_fast: bool,
) -> None:
    errors: list[BaseException] = []
    for future in as_completed(futures):
        index = futures[future]
        try:
            results[index] = future.result()
        except BaseException as exc:
            errors.append(exc)
            if fail_fast:
                for pending in futures:
                    pending.cancel()
                take_finished_results(futures, results, skip=future)
                attach_fail_fast_completed(exc, results)
                raise
    if errors:
        take_finished_results(futures, results)
        attach_fail_fast_completed(errors[0], results)
        raise errors[0]
