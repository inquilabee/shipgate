import threading

import pytest

from shipgate.runtime.parallel import run_parallel


class AttachableError(Exception):
    def __init__(self) -> None:
        self.completed: list[int] = []

    def attach_completed(self, reports: list[int]) -> None:
        self.completed = list(reports)


def test_run_parallel_fail_fast_false_does_not_keyerror():
    def boom(item: int) -> int:
        if item == 1:
            raise RuntimeError("worker failed")
        return item * 10

    with pytest.raises(RuntimeError, match="worker failed"):
        run_parallel([0, 1, 2], boom, fail_fast=False)


def test_run_parallel_preserves_order():
    assert run_parallel([1, 2, 3], lambda x: x) == [1, 2, 3]


def test_run_parallel_fail_fast_attaches_completed():
    first_done = threading.Event()

    def worker(item: int) -> int:
        if item == 0:
            first_done.set()
            return 10
        assert first_done.wait(timeout=5)
        raise AttachableError()

    with pytest.raises(AttachableError) as caught:
        run_parallel([0, 1], worker, fail_fast=True)
    assert caught.value.completed == [10]
