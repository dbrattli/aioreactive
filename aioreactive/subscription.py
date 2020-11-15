import asyncio
import logging
from typing import Awaitable, Callable, Optional, TypeVar

from expression.system.disposable import AsyncDisposable

from .observers import AsyncAwaitableObserver
from .types import AsyncObservable, AsyncObserver

log = logging.getLogger(__name__)

TSource = TypeVar("TSource")


async def run(
    source: AsyncObservable[TSource], observer: Optional[AsyncAwaitableObserver[TSource]] = None, timeout: int = 2
) -> TSource:
    """Run the source with the given observer.

    Similar to `subscribe_async()` but also awaits until the stream
    closes and returns the final value received.

    Args:
        timeout -- Seconds before timing out in case source never closes.

    Returns:
        The last event sent through the stream. If any values have been
        sent through the stream it will return the last value. If the
        stream is closed without any previous values it will throw
        `StopAsyncIteration`. For any other errors it will throw the
        exception.
    """

    # For run we need a noopobserver if no observer is specified to avoid
    # blocking the last single stream in the chain.
    obv: AsyncObserver[TSource] = observer or AsyncAwaitableObserver()
    async with await source.subscribe_async(obv):
        log.debug("run(): waiting for observer ...")
        return await asyncio.wait_for(obv, timeout)


def subscribe_async(obv: AsyncObserver[TSource]) -> Callable[[AsyncObservable[TSource]], Awaitable[AsyncDisposable]]:
    """A pipeable subscribe async.

    Example:
        >>> await pipe(xs, filter(predicate), subscribe_async)
    """

    def _subscribe(source: AsyncObservable[TSource]) -> Awaitable[AsyncDisposable]:
        return source.subscribe_async(obv)

    return _subscribe
