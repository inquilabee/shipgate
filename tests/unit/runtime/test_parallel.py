import pytest

from shipgate.runtime.parallel import run_parallel


def test_run_parallel_fail_fast_false_does_not_keyerror():
    def boom(item: int) -> int:
        if item == 1:
            raise RuntimeError("worker failed")
        return item * 10

    with pytest.raises(RuntimeError, match="worker failed"):
        run_parallel([0, 1, 2], boom, fail_fast=False)


def test_run_parallel_preserves_order():
    assert run_parallel([1, 2, 3], lambda x: x) == [1, 2, 3]
