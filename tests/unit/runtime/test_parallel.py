import threading
import time
from concurrent.futures import Future

import pytest

from shipgate.domain.reports import CheckReport
from shipgate.runtime.parallel import FailFastError, collect_parallel_results, run_parallel


def passed_report(tool_id: str) -> CheckReport:
    return CheckReport(check_id=tool_id, tool_id=tool_id, status="passed", exit_code=0)


def test_run_parallel_fail_fast_false_does_not_keyerror():
    def boom(item: int) -> int:
        if item == 1:
            raise RuntimeError("worker failed")
        return item * 10

    with pytest.raises(RuntimeError, match="worker failed"):
        run_parallel([0, 1, 2], boom, fail_fast=False)


def test_run_parallel_preserves_order():
    assert run_parallel([1, 2, 3], lambda x: x) == [1, 2, 3]


def test_collect_parallel_fail_fast_drains_done_siblings():
    success_a: Future[CheckReport] = Future()
    failing: Future[CheckReport] = Future()
    success_b: Future[CheckReport] = Future()
    first = passed_report("a.tool")
    second = passed_report("b.tool")
    success_a.set_result(first)
    success_b.set_result(second)
    failing.set_exception(
        FailFastError(
            CheckReport(
                check_id="fail.tool",
                tool_id="fail.tool",
                status="failed",
                exit_code=1,
            )
        )
    )
    results: dict[int, CheckReport] = {}
    with pytest.raises(FailFastError) as caught:
        collect_parallel_results(
            {success_a: 0, failing: 1, success_b: 2},
            results,
            fail_fast=True,
        )
    assert caught.value.completed == [first, second]
    assert results == {0: first, 2: second}


def failed_report(tool_id: str) -> CheckReport:
    return CheckReport(check_id=tool_id, tool_id=tool_id, status="failed", exit_code=1)


def test_run_parallel_fail_fast_drains_sibling_that_finishes_after_failure():
    barrier = threading.Barrier(2)

    def work(item: str) -> CheckReport:
        barrier.wait(timeout=5)
        if item == "fail":
            raise FailFastError(failed_report("fail.tool"))
        time.sleep(0.15)
        return passed_report("ok.tool")

    with pytest.raises(FailFastError) as caught:
        run_parallel(["ok", "fail"], work, fail_fast=True)
    assert [report.tool_id for report in caught.value.completed] == ["ok.tool"]


def test_run_parallel_should_cancel_stops_pending():
    started = threading.Event()
    ran: list[int] = []
    lock = threading.Lock()

    def work(item: int) -> int:
        with lock:
            ran.append(item)
        if item == 0:
            started.set()
            return 0
        started.wait(timeout=5)
        time.sleep(0.05)
        return item

    result = run_parallel(
        list(range(10)),
        work,
        fail_fast=False,
        should_cancel=started.is_set,
    )
    assert 0 in result
    assert len(ran) < 10
