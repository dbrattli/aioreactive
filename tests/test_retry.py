import asyncio

import pytest
from expression.core import pipe

import aioreactive as rx
from aioreactive import AsyncObserver
from aioreactive.create import fail
from aioreactive.testing import VirtualTimeEventLoop


class EventLoopPolicy(asyncio.DefaultEventLoopPolicy):
    def get_event_loop(self) -> asyncio.AbstractEventLoop:
        return VirtualTimeEventLoop()


@pytest.fixture(scope="module")
def event_loop_policy():
    return EventLoopPolicy()


@pytest.mark.asyncio(loop_scope="module")
async def test_retry_success():
    """Test that retry successfully retries after initial failure."""
    attempt_count = 0

    def failing_source():
        nonlocal attempt_count
        attempt_count += 1
        if attempt_count < 3:
            return fail(Exception("Temporary failure"))
        return rx.single("Success!")

    # Create an observable that fails twice then succeeds
    xs = rx.defer(failing_source)

    # Retry up to 3 times
    ys = pipe(xs, rx.retry(3))

    # Create a test observer
    values: list[str] = []

    async def asend(value: str) -> None:
        values.append(value)

    obv: AsyncObserver[str] = rx.AsyncAwaitableObserver(asend)
    async with await ys.subscribe_async(obv):
        result = await obv
        assert result == "Success!"
        assert values == ["Success!"]
        assert attempt_count == 3


@pytest.mark.asyncio(loop_scope="module")
async def test_retry_failure():
    """Test that retry propagates errors after exhausting retry attempts."""
    attempt_count = 0

    def always_failing_source():
        nonlocal attempt_count
        attempt_count += 1
        return fail(Exception("Permanent failure"))

    # Create an observable that always fails
    xs = rx.defer(always_failing_source)

    # Retry only once (not enough)
    ys = pipe(xs, rx.retry(1))

    # Should fail after 2 attempts (initial + 1 retry)
    exception = None

    async def athrow(ex: Exception):
        nonlocal exception
        exception = ex

    obv = rx.AsyncAwaitableObserver(athrow=athrow)

    await ys.subscribe_async(obv)

    try:
        await obv
    except Exception as ex:
        assert str(ex) == "Permanent failure"
        assert attempt_count == 2
    else:
        assert False


@pytest.mark.asyncio(loop_scope="module")
async def test_retry_immediate_success():
    """Test that retry passes through successful completions without interference."""
    xs = rx.single("Success!")
    ys = pipe(xs, rx.retry(3))

    values: list[str] = []

    async def asend(value: str) -> None:
        values.append(value)

    obv: AsyncObserver[str] = rx.AsyncAwaitableObserver(asend)
    async with await ys.subscribe_async(obv):
        result = await obv
        assert result == "Success!"
        assert values == ["Success!"]


@pytest.mark.asyncio(loop_scope="module")
async def test_retry_zero_count():
    """Test that retry with zero count doesn't retry."""
    attempt_count = 0

    def always_failing_source():
        nonlocal attempt_count
        attempt_count += 1
        return fail(Exception("Failure"))

    # Create an observable that always fails
    xs = rx.defer(always_failing_source)

    # Retry zero times (no retries)
    ys = pipe(xs, rx.retry(0))

    # Should fail immediately without retrying
    exception = None

    async def athrow(ex: Exception):
        nonlocal exception
        exception = ex

    obv = rx.AsyncAwaitableObserver(athrow=athrow)

    await ys.subscribe_async(obv)

    try:
        await obv
    except Exception as ex:
        assert str(ex) == "Failure"
        assert attempt_count == 1
    else:
        assert False


@pytest.mark.asyncio(loop_scope="module")
async def test_retry_subscription_cancel():
    """Test that retry properly handles subscription cancellation."""
    xs: rx.AsyncSubject[int] = rx.AsyncSubject()
    result: list[int] = []

    ys = pipe(xs, rx.retry(3))

    async def asend(value: int) -> None:
        result.append(value)
        # Get the subscription from the context and dispose it
        await asyncio.sleep(0)

    async with await ys.subscribe_async(rx.AsyncAnonymousObserver(asend)) as subscription:
        await xs.asend(10)
        await asyncio.sleep(0)
        await subscription.dispose_async()
        await xs.asend(20)

    assert result == [10]
