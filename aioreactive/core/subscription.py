import logging
import asyncio
from typing import TypeVar, Generic, Optional
from collections.abc import Awaitable

from aioreactive.abc import AsyncDisposable

from .typing import AsyncObservable, AsyncObserver
from .utils import noopobserver
from .streams import AsyncSingleStream
from .observers import AsyncAnonymousObserver

log = logging.getLogger(__name__)

T = TypeVar("T")


class AsyncSubscriptionFactory(Awaitable, AsyncDisposable):
    """Async stream factory.

    A helper class that makes it possible to subscribe both
    using await and async-with. You will most likely not use this class
    directly, but it will created when using subscribe()."""

    def __init__(self, source, observer=None):
        self._source = source
        self._observer = observer

        self._subscription = None

    async def create(self) -> AsyncDisposable:
        """Awaits stream creation.

        Awaits until stream has been created, and returns the new
        stream."""

        self._subscription = await chain(self._source, self._observer)
        return self._subscription

    async def adispose(self) -> None:
        """Closes stream."""
        await self._subscription.adispose()

    async def __aenter__(self) -> AsyncDisposable:
        """Awaits stream creation."""
        return await self.create()

    def __await__(self):
        """Await stream creation."""
        return self.create().__await__()


async def chain(source, observer) -> AsyncDisposable:
    """Chains an async observer with an async observable.

    Performs the chaining done internally by most operators. A much
    more light-weight version of subscribe()."""

    return await source.__asubscribe__(observer)


def subscribe(source: AsyncObservable, observer: Optional[AsyncObserver]=None) -> AsyncSubscriptionFactory:
    """Start streaming source into observer.

    Returns an AsyncStreamFactory that is lazy in the sense that it will
    not start the source before it's either awaited or entered using
    async-with.

    Examples:

    1. Awaiting stream with explicit cancel:

    stream = await subscribe(source, observer)
    async for x in stream:
        print(x)

    stream.cancel()

    2. Start streaming with a context manager:

    async with subscribe(source, observer) as stream:
        async for x in stream:
            print(x)

    3. Start streaming without a specific observer

    async with subscribe(source) as stream:
        async for x in stream:
            print(x)

    Keyword arguments:
    observer -- Optional AsyncObserver that will receive all events sent through
        the stream.

    Returns AsyncStreamFactory that may either be awaited or entered
    using async-for.
    """
    return AsyncSubscriptionFactory(source, observer)


async def run(source: AsyncObservable[T], observer: Optional[AsyncObserver]=None, timeout: int=2) -> T:
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
    observer = observer or AsyncAnonymousObserver()
    await subscribe(source, observer)
    return await asyncio.wait_for(observer, timeout)
