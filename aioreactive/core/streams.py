import logging
from asyncio import Future
from typing import TypeVar, Generic
from typing import AsyncIterable, AsyncIterator
from abc import abstractmethod

from .typing import AsyncObserver
from .futures import AsyncMultiFuture, chain_future
from .observers import AsyncIteratorObserver
from .observables import AsyncObservable
from .utils import noopobserver

log = logging.getLogger(__name__)

T = TypeVar("T")


class AsyncStreamIterable(AsyncIterable):
    async def __aiter__(self) -> AsyncIterator:
        """Iterate asynchronously.

        Transforms the async source to an async iterable. The source
        will await for the iterator to pick up the value before
        continuing to avoid queuing values.
        """

        _observer = AsyncIteratorObserver()
        await self.__asubscribe__(_observer)
        return _observer

    @abstractmethod
    async def __asubscribe__(self, sink: AsyncObserver):
        return NotImplemented


class AsyncSingleStream(AsyncMultiFuture[T], AsyncObservable[T], AsyncStreamIterable):

    """An stream with a single sink.

    Both an async multi future and async iterable. Thus you may
    .cancel() it to stop streaming, async iterate it using async-for.

    The AsyncSingleStream is cold in the sense that it will await an
    observer before forwarding any events.
    """

    def __init__(self) -> None:
        super().__init__()

        self._wait = Future()  # type: Future
        self._observer = None  # type: AsyncObserver

    async def asend(self, value: T):
        log.debug("AsyncSingleStream:asend(%s)", value)

        if self.done():
            return

        await super().asend(value)

        # AsyncSingleStreams are cold and will await a sink.
        if self._observer is None:
            log.debug("AsyncSingleStream:asend:awaiting start")
            await self._wait
            log.debug("AsyncSingleStream:asend:awaiting:done")

        await self._observer.asend(value)

    async def athrow(self, ex: Exception) -> None:
        if self.done():
            return

        await super().athrow(ex)

        if self._observer is None:
            log.debug("athrow:AsyncSingleStream:awaiting start")
            await self._wait

        await self._observer.athrow(ex)

    async def aclose(self) -> None:
        log.debug("AsyncSingleStream:aclose()")
        if self.done():
            return

        await super().aclose()

        if self._observer is None:
            log.debug("AsyncSingleStream:aclose:awaiting start")
            await self._wait

        await self._observer.aclose()

    async def __asubscribe__(self, observer: AsyncObserver) -> "AsyncSingleStream":
        """Start streaming."""

        self._observer = observer
        if not self._wait.done():
            self._wait.set_result(True)
        return self


class AsyncMultiStream(AsyncMultiFuture[T], AsyncObservable[T]):
    """An stream with a multiple observers.

    Both an async multi future and async iterable. Thus you may
    .cancel() it to stop streaming, async iterate it using async-for.

    The AsyncMultiStream is hot in the sense that it will drop events
    if there are currently no observer running.
    """

    def __init__(self) -> None:
        super().__init__()
        self._observers = {}  # type: Dict[AsyncObserver, AsyncSingleStream]

    async def asend(self, value: T) -> None:
        if self.done():
            return

        await super().asend(value)

        for stream in list(self._observers):
            await stream.asend(value)
        else:
            log.info("AsyncMultiStream.asend, dropped value")

    async def athrow(self, ex: Exception) -> None:
        if self.done():
            return

        await super().athrow(ex)

        for stream in list(self._observers):
            await stream.athrow(ex)
        else:
            log.info("AsyncMultiStream.athrow, dropped exception: ", ex)

    async def aclose(self) -> None:
        if self.done():
            return

        await super().aclose()

        for stream in list(self._observers):
            await stream.aclose()
        else:
            log.info("AsyncMultiStream.aclose, dropped close")

    async def __asubscribe__(self, observer: AsyncObserver) -> AsyncSingleStream:
        """Start streaming."""

        if isinstance(observer, AsyncSingleStream):
            stream = observer
        else:
            stream = await AsyncSingleStream().__asubscribe__(observer)
        self._observers[observer] = stream

        def done(sub: Future) -> None:
            log.debug("AsyncMultiFuture:done()")
            if stream in self._observers:
                del self._observers[stream]

        stream.add_done_callback(done)
        return stream


# Alias
AsyncStream = AsyncMultiStream
