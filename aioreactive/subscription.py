import asyncio
import logging
from typing import Optional, TypeVar

from .observers import AsyncAwaitableObserver
from .types import AsyncObservable, AsyncObserver

log = logging.getLogger(__name__)

TSource = TypeVar("TSource")


async def run(
    source: AsyncObservable[TSource], observer: Optional[AsyncAwaitableObserver[TSource]] = None, timeout: int = 2
) -> TSource:
    """Run the source with the given observer.

    Similar to subscribe() but also awaits until the stream closes and
    returns the final value.

    Keyword arguments:
    timeout -- Seconds before timing out in case source never closes.

    Returns last event sent through the stream. If any values have been
    sent through the stream it will return the last value. If the stream
    is closed without any previous values it will throw
    StopAsyncIteration. For any other errors it will throw the
    exception.
    """

    # For run we need a noopobserver if no observer is specified to avoid
    # blocking the last single stream in the chain.
    observer_: AsyncObserver[TSource] = observer or AsyncAwaitableObserver()
    await source.subscribe_async(observer_)
    log.debug("run(): waiting for observer ...")
    return await asyncio.wait_for(observer_, timeout)
