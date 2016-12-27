import logging
import asyncio
from typing import TypeVar, Generic, Optional
from collections.abc import Awaitable

from aioreactive.abc import AsyncDisposable

from .typing import AsyncObservable, AsyncObserver
from .futures import AsyncMultiFuture, chain_future
from .observers import AsyncIteratorObserver
from .utils import noopobserver
from .streams import AsyncSingleStream

log = logging.getLogger(__name__)

T = TypeVar("T")


class AsyncStreamFactory(Awaitable, AsyncDisposable):
    """Async stream factory.

    A helper class that makes it possible to subscribe() streaming both
    using await and async-with. You will most likely not use this class
    directly, but it will created when using subscribe()."""

    def __init__(self, source, sink=None):
        self._source = source
        self._observer = sink

        self._stream = None

    async def create(self) -> AsyncSingleStream:
        """Awaits stream creation.

        Awaits until stream has been created, and returns the new
        stream."""

        if self._observer is not None:
            down_stream = await chain(AsyncSingleStream(), self._observer)
        else:
            down_stream = AsyncSingleStream()

        up_stream = await chain(self._source, down_stream)
        self._stream = chain_future(down_stream, up_stream)
        return self._stream

    async def adispose(self) -> None:
        """Closes stream."""
        self._stream.cancel()

    async def __aenter__(self) -> AsyncSingleStream:
        """Awaits stream creation."""
        return await self.create()

    def __await__(self):
        """Await stream creation."""
        return self.create().__await__()


async def chain(source, sink):
    """Chains an async sink with an async source.

    Performs the chaining done internally by most operators. A much
    more light-weight version of subscribe()."""

    return await source.__asubscribe__(sink)


def subscribe(source: AsyncObservable, sink: Optional[AsyncObserver]=None) -> AsyncStreamFactory:
    """Start streaming source into sink.

    Returns an AsyncStreamFactory that is lazy in the sense that it will
    not start the source before it's either awaited or entered using
    async-with.

    Examples:

    1. Awaiting stream with explicit cancel:

    stream = await subscribe(source, sink)
    async for x in stream:
        print(x)

    stream.cancel()

    2. Start streaming with a context manager:

    async with subscribe(source, sink) as stream:
        async for x in stream:
            print(x)

    3. Start streaming without a specific sink

    async with subscribe(source) as stream:
        async for x in stream:
            print(x)

    Keyword arguments:
    sink -- Optional AsyncObserver that will receive all events sent through
        the stream.

    Returns AsyncStreamFactory that may either be awaited or entered
    using async-for.
    """
    return AsyncStreamFactory(source, sink)


async def run(source: AsyncObservable[T], sink: Optional[AsyncObserver]=None, timeout: int=2) -> T:
    """Run the source with the given sink.

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

    # For run we need a noopobserver if no sink is specified to avoid
    # blocking the last single stream in the chain.
    sink = sink or noopobserver
    return await asyncio.wait_for(await subscribe(source, sink), timeout)
