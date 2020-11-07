import logging
from typing import Awaitable, Callable, Iterable, Tuple, TypeVar

from expression.core import aio
from expression.system import AsyncDisposable, CancellationToken, CancellationTokenSource

from .observables import AsyncAnonymousObservable
from .observers import AsyncObserver, safe_observer
from .types import AsyncObservable

TSource = TypeVar("TSource")

log = logging.getLogger(__name__)


def canceller() -> Tuple[AsyncDisposable, CancellationToken]:
    cts = CancellationTokenSource()

    async def cancel() -> None:
        cts.cancel()

    return (AsyncDisposable.create(cancel), cts.token)


def create(subscribe: Callable[[AsyncObserver[TSource]], Awaitable[AsyncDisposable]]) -> AsyncObservable[TSource]:
    """Creates an async observable (`AsyncObservable{'TSource}`) from the
    given subscribe function.
    """
    return AsyncAnonymousObservable(subscribe)


def of_async_worker(
    worker: Callable[[AsyncObserver[TSource], CancellationToken], Awaitable[None]]
) -> AsyncObservable[TSource]:
    """Create async observable from async worker function"""

    log.debug("of_async_worker()")

    async def subscribe_async(aobv: AsyncObserver[TSource]) -> AsyncDisposable:
        log.debug("of_async_worker:subscribe_async()")
        disposable, token = canceller()
        safe_obv = safe_observer(aobv, disposable)

        aio.start(worker(safe_obv, token), token)
        return disposable

    return AsyncAnonymousObservable(subscribe_async)


def of_async(workflow: Awaitable[TSource]) -> AsyncObservable[TSource]:
    """Returns the async observable sequence whose single element is the result of the given async workflow."""

    async def worker(obv: AsyncObserver[TSource], _: CancellationToken) -> None:
        try:
            result = await workflow
            await obv.asend(result)
            await obv.aclose()
        except Exception as ex:
            await obv.athrow(ex)

    return of_async_worker(worker)


def single(value: TSource) -> AsyncObservable[TSource]:
    """Returns an observable sequence containing the single specified element."""

    async def subscribe_async(aobv: AsyncObserver[TSource]) -> AsyncDisposable:
        safe_obv = safe_observer(aobv, AsyncDisposable.empty())

        await safe_obv.asend(value)
        await safe_obv.aclose()
        return AsyncDisposable.empty()

    return AsyncAnonymousObservable(subscribe_async)


def empty() -> AsyncObservable[TSource]:
    """Returns an observable sequence with no elements."""

    async def subscribe_async(aobv: AsyncObserver[TSource]) -> AsyncDisposable:
        await aobv.aclose()
        return AsyncDisposable.empty()

    return AsyncAnonymousObservable(subscribe_async)


def never() -> AsyncObservable[TSource]:
    """Returns an empty observable sequence that never completes."""

    async def subscribe_async(_: AsyncObserver[TSource]) -> AsyncDisposable:
        return AsyncDisposable.empty()

    return AsyncAnonymousObservable(subscribe_async)


def fail(error: Exception) -> AsyncObservable[TSource]:
    """Returns the observable sequence that terminates exceptionally
    with the specified exception."""

    async def worker(obv: AsyncObserver[TSource], _: CancellationToken) -> None:
        await obv.athrow(error)

    return of_async_worker(worker)


def of_seq(xs: Iterable[TSource]) -> AsyncObservable[TSource]:
    """Returns the async observable sequence whose elements are pulled
    from the given enumerable sequence."""

    async def worker(obv: AsyncObserver[TSource], token: CancellationToken) -> None:
        log.debug("of_seq:worker()")
        for x in xs:
            try:
                log.debug("of_seq:asend(%s)", x)
                await obv.asend(x)
            except Exception as ex:
                await obv.athrow(ex)

        await obv.aclose()

    return of_async_worker(worker)


def defer(factory: Callable[[], AsyncObservable[TSource]]) -> AsyncObservable[TSource]:
    """Returns an observable sequence that invokes the specified factory function whenever a new observer subscribes."""

    async def subscribe_async(aobv: AsyncObserver[TSource]) -> AsyncDisposable:
        try:
            result = factory()
        except Exception as ex:
            result = fail(ex)

        return await result.subscribe_async(aobv)

    return AsyncAnonymousObservable(subscribe_async)


def interval(msecs: int, period: int) -> AsyncObservable[int]:
    """Returns an observable sequence that triggers the increasing
    sequence starting with 0 after the given msecs, and the after
    each period."""

    async def subscribe_async(aobv: AsyncObserver[int]) -> AsyncDisposable:
        cancel, token = canceller()

        async def handler(msecs: int, next: TSource) -> None:
            await aio.sleep(msecs)
            await aobv.asend(next)

            if period > 0:
                await handler(period, next + 1)
            else:
                await aobv.aclose()

        aio.start(handler(msecs, 0), token)
        return cancel

    return AsyncAnonymousObservable(subscribe_async)


def timer(dueTime: int) -> AsyncObservable[int]:
    """Returns an observable sequence that triggers the value 0
    after the given duetime in milliseconds."""

    return interval(dueTime, 0)
