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


def parallel_should_stop(
    *,
    fail_fast: bool,
    should_cancel: Callable[[], bool] | None,
    exc: BaseException | None = None,
) -> bool:
    return (
        fail_fast
        or isinstance(exc, FailFastError)
        or (should_cancel is not None and should_cancel())
    )


def cancel_futures(futures: dict[Future[R], int]) -> None:
    for pending in futures:
        pending.cancel()


def run_parallel(
    items: list[T],
    fn: Callable[[T], R],
    *,
    fail_fast: bool = False,
    should_cancel: Callable[[], bool] | None = None,
) -> list[R]:
    if not items:
        return []
    if len(items) == 1:
        return [fn(items[0])]

    results: dict[int, R] = {}
    futures: dict[Future[R], int] = {}
    try:
        with ThreadPoolExecutor(max_workers=min(len(items), 8)) as pool:
            futures = {pool.submit(fn, item): index for index, item in enumerate(items)}
            collect_parallel_results(
                futures,
                results,
                fail_fast=fail_fast,
                should_cancel=should_cancel,
            )
    except FailFastError as exc:
        take_finished_results(futures, results)
        attach_fail_fast_completed(exc, results)
        raise
    take_finished_results(futures, results)
    return [results[i] for i in range(len(items)) if i in results]


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
    should_cancel: Callable[[], bool] | None = None,
) -> None:
    errors: list[BaseException] = []
    for future in as_completed(futures):
        index = futures[future]
        try:
            results[index] = future.result()
        except BaseException as exc:
            errors.append(exc)
            if parallel_should_stop(fail_fast=fail_fast, should_cancel=should_cancel, exc=exc):
                cancel_futures(futures)
                take_finished_results(futures, results, skip=future)
                attach_fail_fast_completed(exc, results)
                raise
        if parallel_should_stop(fail_fast=False, should_cancel=should_cancel):
            cancel_futures(futures)
            break
    if errors:
        take_finished_results(futures, results)
        attach_fail_fast_completed(errors[0], results)
        raise errors[0]
