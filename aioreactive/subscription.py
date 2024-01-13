import asyncio
import logging
from collections.abc import Awaitable, Callable
from typing import TypeVar

from expression.system.disposable import AsyncDisposable

from .observers import AsyncAwaitableObserver
from .types import AsyncObservable, AsyncObserver


log = logging.getLogger(__name__)

_TSource = TypeVar("_TSource")


async def run(
    source: AsyncObservable[_TSource],
    observer: AsyncAwaitableObserver[_TSource] | None = None,
    timeout: int = 2,
) -> _TSource:
    """Run the source with the given observer.

    Similar to `subscribe_async()` but also awaits until the stream
    closes and returns the final value received.

    Args:
        source: The source observable.
        observer: The observer to subscribe to the source.
        timeout: Seconds before timing out in case source never closes.

    Returns:
        The last event sent through the stream. If any values have been
        sent through the stream it will return the last value. If the
        stream is closed without any previous values it will throw
        `StopAsyncIteration`. For any other errors it will throw the
        exception.
    """
    # For run we need a noopobserver if no observer is specified to avoid
    # blocking the last single stream in the chain.
    obv: AsyncAwaitableObserver[_TSource] = observer or AsyncAwaitableObserver()
    async with await source.subscribe_async(obv):
        log.debug("run(): waiting for observer ...")
        return await asyncio.wait_for(obv, timeout)


def subscribe_async(
    obv: AsyncObserver[_TSource],
) -> Callable[[AsyncObservable[_TSource]], Awaitable[AsyncDisposable]]:
    """A pipeable subscribe async.

    Example:
        >>> await pipe(xs, filter(predicate), subscribe_async)
    """

    def _subscribe(source: AsyncObservable[_TSource]) -> Awaitable[AsyncDisposable]:
        return source.subscribe_async(obv)

    return _subscribe
