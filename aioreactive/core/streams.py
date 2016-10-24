import logging
import asyncio
from asyncio import Future
from typing import TypeVar, Generic, Dict, Optional
from typing import AsyncIterable, AsyncIterator
from collections.abc import Awaitable
from abc import abstractmethod


from aioreactive.core.abc import AsyncCancellable
from .typing import AsyncSource, AsyncSink
from .futures import AsyncMultiFuture, chain_future
from .sinks import AsyncIteratorSink
from .utils import noopsink

log = logging.getLogger(__name__)

T = TypeVar("T")


class AsyncStreamIterable(AsyncIterable):
    async def __aiter__(self) -> AsyncIterator:
        """Iterate asynchronously.

        Transforms the async source to an async iterable. The source
        will await for the iterator to pick up the value before
        continuing to avoid queuing values.
        """

        _sink = AsyncIteratorSink()
        await self.__astart__(_sink)
        return _sink

    @abstractmethod
    async def __astart__(self, sink: AsyncSink):
        return NotImplemented


class AsyncSingleStream(AsyncMultiFuture, AsyncStreamIterable, Generic[T]):

    """An stream with a single sink.

    Both an async multi future and async iterable. Thus you may
    .cancel() it to stop streaming, async iterate it using async-for.

    The AsyncSingleStream is cold in the sense that it will await a
    starting sink before forwarding any events.
    """

    def __init__(self) -> None:
        super().__init__()

        self._wait = Future()  # type: Future
        self._sink = None  # type: AsyncSink

    async def asend(self, value: T):
        log.debug("AsyncSingleStream:asend(%s)", value)

        if self.done():
            return

        await super().asend(value)

        # AsyncSingleStreams are cold and will await a sink.
        if self._sink is None:
            log.debug("AsyncSingleStream:asend:awaiting start")
            await self._wait
            log.debug("AsyncSingleStream:asend:awaiting:done")

        await self._sink.asend(value)

    async def athrow(self, ex: Exception) -> None:
        if self.done():
            return

        await super().athrow(ex)

        if self._sink is None:
            log.debug("athrow:AsyncSingleStream:awaiting start")
            await self._wait

        await self._sink.athrow(ex)

    async def aclose(self) -> None:
        log.debug("AsyncSingleStream:aclose()")
        if self.done():
            return

        await super().aclose()

        if self._sink is None:
            log.debug("AsyncSingleStream:aclose:awaiting start")
            await self._wait

        await self._sink.aclose()

    async def __astart__(self, sink: AsyncSink) -> "AsyncSingleStream":
        """Start streaming."""

        self._sink = sink
        if not self._wait.done():
            self._wait.set_result(True)
        return self


class AsyncMultiStream(AsyncMultiFuture, Generic[T]):
    """An stream with a multiple sinks.

    Both an async multi future and async iterable. Thus you may
    .cancel() it to stop streaming, async iterate it using async-for.

    The AsyncMultiStream is hot in the sense that it will drop events
    if there are currently no sinks running.
    """

    def __init__(self) -> None:
        super().__init__()
        self._sinks = {}  # type: Dict[AsyncSink, AsyncSingleStream]

    async def asend(self, value: T) -> None:
        if self.done():
            return

        await super().asend(value)

        for stream in list(self._sinks):
            await stream.asend(value)
        else:
            log.info("AsyncMultiFuture.athrow, value dropped")

    async def athrow(self, ex: Exception) -> None:
        if self.done():
            return

        await super().athrow(ex)

        for stream in list(self._sinks):
            await stream.athrow(ex)
        else:
            log.info("AsyncMultiFuture.athrow, exception dropped")

    async def aclose(self) -> None:
        if self.done():
            return

        await super().aclose()

        for stream in list(self._sinks):
            await stream.aclose()
        else:
            log.info("AsyncMultiFuture.athrow, close dropped")

    async def __astart__(self, sink: AsyncSink) -> AsyncSingleStream:
        """Start streaming."""

        if isinstance(sink, AsyncSingleStream):
            stream = sink
        else:
            stream = await chain(AsyncSingleStream(), sink)
        self._sinks[sink] = stream

        def done(sub: Future) -> None:
            log.debug("AsyncMultiFuture:done()")
            if stream in self._sinks:
                del self._sinks[stream]

        stream.add_done_callback(done)
        return stream


# Alias
AsyncStream = AsyncMultiStream


class AsyncStreamFactory(Awaitable, AsyncCancellable):
    """Async stream factory.

    A helper class that makes it possible to start() streaming both
    using await and async-with. You will most likely not use this class
    directly, but it will created when using start()."""

    def __init__(self, source, sink=None):
        self._source = source
        self._sink = sink

        self._stream = None

    async def create(self) -> AsyncSingleStream:
        """Awaits stream creation.

        Awaits until stream has been created, and returns the new
        stream."""

        if self._sink is not None:
            down_stream = await chain(AsyncSingleStream(), self._sink)
        else:
            down_stream = AsyncSingleStream()

        up_stream = await chain(self._source, down_stream)
        self._stream = chain_future(down_stream, up_stream)
        return self._stream

    async def acancel(self) -> None:
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
    more light-weight version of start()."""

    return await source.__astart__(sink)


def start(source: AsyncSource, sink: Optional[AsyncSink]=None) -> AsyncStreamFactory:
    """Start streaming source into sink.

    Returns an AsyncStreamFactory that is lazy in the sense that it will
    not start the source before it's either awaited or entered using
    async-with.

    Examples:

    1. Awaiting stream with explicit cancel:

    stream = await start(source, sink)
    async for x in stream:
        print(x)

    stream.cancel()

    2. Start streaming with a context manager:

    async with start(source, sink) as stream:
        async for x in stream:
            print(x)

    3. Start streaming without a specific sink

    async with start(source) as stream:
        async for x in stream:
            print(x)

    Keyword arguments:
    sink -- Optional AsyncSink that will receive all events sent through
        the stream.

    Returns AsyncStreamFactory that may either be awaited or entered
    using async-for.
    """
    return AsyncStreamFactory(source, sink)


async def run(source: AsyncSource[T], sink: Optional[AsyncSink]=None, timeout: int=2) -> T:
    """Run the source with the given sink.

    Similar to start() but also awaits until the stream closes and
    returns the final value.

    Keyword arguments:
    timeout -- Seconds before timing out in case source never closes.

    Returns last event sent through the stream. If any values have been
    sent through the stream it will return the last value. If the stream
    is closed without any previous values it will throw
    StopAsyncIteration. For any other errors it will throw the
    exception.
    """

    # For run we need a noopsink if no sink is specified to avoid
    # blocking the last single stream in the chain.
    sink = sink or noopsink
    return await asyncio.wait_for(await start(source, sink), timeout)
