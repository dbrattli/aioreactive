import asyncio
import logging
from asyncio import Task
from collections.abc import AsyncIterable, Awaitable, Callable, Iterable
from typing import Any, TypeVar

from expression import TailCall, TailCallResult, tailrec_async
from expression.core import aiotools
from expression.system import (
    AsyncDisposable,
    CancellationToken,
    CancellationTokenSource,
)

from .observables import AsyncAnonymousObservable
from .observers import AsyncObserver, safe_observer
from .types import AsyncObservable


TSource = TypeVar("TSource")

log = logging.getLogger(__name__)


def canceller() -> tuple[AsyncDisposable, CancellationToken]:
    cts = CancellationTokenSource()

    async def cancel() -> None:
        log.debug("cancller, cancelling!")
        cts.cancel()

    return AsyncDisposable.create(cancel), cts.token


def create(subscribe: Callable[[AsyncObserver[TSource]], Awaitable[AsyncDisposable]]) -> AsyncObservable[TSource]:
    """Create an async observable.

    Creates an `AsyncObservable[TSource]` from the given subscribe
    function.
    """
    return AsyncAnonymousObservable(subscribe)


def of_async_worker(worker: Callable[[AsyncObserver[Any], CancellationToken], Awaitable[None]]) -> AsyncObservable[Any]:
    """Create async observable from async worker function."""
    log.debug("of_async_worker()")

    async def subscribe_async(aobv: AsyncObserver[Any]) -> AsyncDisposable:
        log.debug("of_async_worker:subscribe_async()")
        disposable, token = canceller()
        safe_obv = safe_observer(aobv, disposable)

        aiotools.start(worker(safe_obv, token), token)
        return disposable

    return AsyncAnonymousObservable(subscribe_async)


def of_async(workflow: Awaitable[TSource]) -> AsyncObservable[TSource]:
    """Create from async workflow.

    Returns the async observable sequence whose single element is the
    result of the given async workflow.
    """

    async def worker(obv: AsyncObserver[TSource], _: CancellationToken) -> None:
        try:
            result = await workflow
            # Note to self. If workflow is or gets cancelled we will jump straight to `finally`.
            await obv.asend(result)
        except Exception as ex:
            await obv.athrow(ex)
        finally:
            await obv.aclose()

    return of_async_worker(worker)


def of_async_iterable(iterable: AsyncIterable[TSource]) -> AsyncObservable[TSource]:
    tasks: set[Task[Any]] = set()

    async def subscribe_async(observer: AsyncObserver[TSource]) -> AsyncDisposable:
        async def cancel() -> None:
            if task:
                task.cancel()

        sub = AsyncDisposable.create(cancel)

        async def worker() -> None:
            async for value in iterable:
                try:
                    await observer.asend(value)
                except Exception as ex:
                    await observer.athrow(ex)
                    return

            await observer.aclose()
            tasks.remove(task)

        try:
            task = asyncio.create_task(worker())
        except Exception as ex:
            log.debug(f"FromIterable:worker(), Exception: {ex}")
            await observer.athrow(ex)
        else:
            tasks.add(task)
        return sub

    return AsyncAnonymousObservable(subscribe_async)


def single(value: TSource) -> AsyncObservable[TSource]:
    """Create from a single item.

    Returns an observable sequence containing the single specified
    element.
    """

    async def subscribe_async(aobv: AsyncObserver[TSource]) -> AsyncDisposable:
        safe_obv = safe_observer(aobv, AsyncDisposable.empty())

        await safe_obv.asend(value)
        await safe_obv.aclose()
        return AsyncDisposable.empty()

    return AsyncAnonymousObservable(subscribe_async)


def empty() -> AsyncObservable[Any]:
    """Returns an observable sequence with no elements."""

    async def subscribe_async(aobv: AsyncObserver[Any]) -> AsyncDisposable:
        await aobv.aclose()
        return AsyncDisposable.empty()

    return AsyncAnonymousObservable(subscribe_async)


def never() -> AsyncObservable[Any]:
    """Returns an empty observable sequence that never completes."""

    async def subscribe_async(_: AsyncObserver[Any]) -> AsyncDisposable:
        return AsyncDisposable.empty()

    return AsyncAnonymousObservable(subscribe_async)


def fail(error: Exception) -> AsyncObservable[Any]:
    """Create failing observable.

    Returns the observable sequence that terminates exceptionally
    with the specified exception.
    """

    async def worker(obv: AsyncObserver[Any], _: CancellationToken) -> None:
        await obv.athrow(error)

    return of_async_worker(worker)


def of_seq(xs: Iterable[TSource]) -> AsyncObservable[TSource]:
    """Create async observable from sequence.

    Returns the async observable sequence whose elements are pulled from
    the given enumerable sequence.
    """

    async def worker(obv: AsyncObserver[TSource], token: CancellationToken) -> None:
        log.debug("of_seq:worker()")
        for x in xs:
            token.throw_if_cancellation_requested()
            log.debug("of_seq:asend(%s)", x)

            try:
                await obv.asend(x)
            except Exception as ex:
                await obv.athrow(ex)

        await obv.aclose()

    return of_async_worker(worker)


def defer(factory: Callable[[], AsyncObservable[TSource]]) -> AsyncObservable[TSource]:
    """Defer observable.

    Returns an observable sequence that invokes the specified factory
    function whenever a new observer subscribes.
    """

    async def subscribe_async(aobv: AsyncObserver[TSource]) -> AsyncDisposable:
        try:
            result = factory()
        except Exception as ex:
            result = fail(ex)

        return await result.subscribe_async(aobv)

    return AsyncAnonymousObservable(subscribe_async)


def interval(seconds: float, period: float) -> AsyncObservable[int]:
    """Create observable interval.

    Returns an observable sequence that triggers the increasing
    sequence starting with 0 after the given msecs, and the after each
    period.
    """

    async def subscribe_async(aobv: AsyncObserver[int]) -> AsyncDisposable:
        cancel, token = canceller()

        @tailrec_async
        async def handler(seconds: float, next: int) -> "TailCallResult[None, [float, int]]":
            await asyncio.sleep(seconds)
            await aobv.asend(next)

            if not period:
                await aobv.aclose()
                return None

            return TailCall[float, int](period, next + 1)

        aiotools.start(handler(seconds, 0), token)
        return cancel

    return AsyncAnonymousObservable(subscribe_async)


def timer(due_time: float) -> AsyncObservable[int]:
    """Create observable timer.

    Returns an observable sequence that triggers the value 0
    after the given duetime in milliseconds.
    """
    return interval(due_time, 0)
