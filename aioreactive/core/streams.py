import logging
import asyncio
from asyncio import Future
from typing import TypeVar, Generic, Dict, Optional
from typing import AsyncIterable, AsyncIterator
from collections.abc import Awaitable

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


class AsyncSingleStream(AsyncMultiFuture, AsyncStreamIterable, Generic[T]):

    """An asynch multi-value future.

    Both a future and async sink. The future resolves with the last
    value before the sink is closed. A close without any values sent is
    the same as cancelling the future.
    """

    def __init__(self) -> None:
        super().__init__()

        self._wait = Future()
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
    """The Async Stream.

    The stream is both a source and a sink. Thus you can both listen
    to it and send values to it. Any values send will be forwarded to
    all FuncSinks.
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


class AsyncStreamFactory(Awaitable):
    """A helper class that makes it possible to start streaming both
    using await and async-with."""

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

    async def __aenter__(self) -> AsyncSingleStream:
        """Awaits stream creation."""
        return await self.create()

    async def __aexit__(self, type, value, traceback) -> None:
        """Closes stream."""
        self._stream.cancel()

    def __await__(self) -> AsyncSingleStream:
        """Await stream creation."""
        return self.create().__await__()


async def chain(source, sink):
    """Chains an async sink with an async source.

    Performs the chaining done internally by most operators."""

    return await source.__astart__(sink)


def start(source: AsyncSource, sink: Optional[AsyncSink]=None) -> AsyncStreamFactory:
    return AsyncStreamFactory(source, sink)


async def run(source: AsyncSource[T], sink: Optional[AsyncSink]=None, timeout: int=2) -> T:
    """Awaits until subscription closes and returns the final value"""

    # For run we need a noopsink if no sink is specified to avoid
    # blocking the last single stream in the chain.
    sink = sink or noopsink
    return await asyncio.wait_for(await start(source, sink), timeout)
