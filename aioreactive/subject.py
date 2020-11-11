import logging
from asyncio import Future
from typing import List, Optional, TypeVar

from expression.system import AsyncDisposable

from .observables import AsyncObservable
from .types import AsyncObserver

log = logging.getLogger(__name__)

TSource = TypeVar("TSource")


class AsyncSingleSubject(AsyncObserver[TSource], AsyncObservable[TSource], AsyncDisposable):

    """An stream with a single sink.

    Both an async multi future and async iterable. Thus you may
    .cancel() it to stop streaming, async iterate it using async-for.

    The AsyncSingleStream is cold in the sense that it will await an
    observer before forwarding any events.
    """

    def __init__(self) -> None:
        super().__init__()

        self._wait: Future[bool] = Future()
        self._observer: Optional[AsyncObserver[TSource]] = None

    async def asend(self, value: TSource):
        log.debug("AsyncSingleStream:asend(%s)", str(value))

        # AsyncSingleStreams are cold and will await a sink.
        while self._observer is None:
            log.debug("AsyncSingleStream:asend:awaiting start")
            await self._wait
            log.debug("AsyncSingleStream:asend:awaiting:done")

        await self._observer.asend(value)

    async def athrow(self, error: Exception) -> None:
        log.debug("AsyncSingleStream:athrow()")

        while self._observer is None:
            await self._wait

        await self._observer.athrow(error)

    async def aclose(self) -> None:
        log.debug("AsyncSingleStream:aclose()")

        while self._observer is None:
            log.debug("AsyncSingleStream:aclose:awaiting start")
            await self._wait

        await self._observer.aclose()

    async def adispose(self):
        self._observer = None
        self._is_stopped = True

    async def subscribe_async(self, observer: AsyncObserver[TSource]) -> AsyncDisposable:
        """Start streaming."""

        self._observer = observer

        if not self._wait.done():
            self._wait.set_result(True)

        return AsyncDisposable.create(self.adispose)


class AsyncMultiSubject(AsyncObserver[TSource], AsyncObservable[TSource]):
    """An stream with a multiple observers.

    Both an async multi future and async iterable. Thus you may
    .cancel() it to stop streaming, async iterate it using async-for.

    The AsyncMultiStream is "hot" in the sense that it will drop events
    if there are currently no observer running.
    """

    def __init__(self) -> None:
        super().__init__()
        self._observers: List[AsyncObserver[TSource]] = []

    async def asend(self, value: TSource) -> None:
        for obv in list(self._observers):
            await obv.asend(value)

    async def athrow(self, error: Exception) -> None:
        for obv in list(self._observers):
            await obv.athrow(error)

    async def aclose(self) -> None:
        for obv in list(self._observers):
            await obv.aclose()

    async def subscribe_async(self, observer: AsyncObserver[TSource]) -> AsyncDisposable:
        """Subscribe."""

        log.debug("AsyncMultiStream:subscribe_async()")

        self._observers.append(observer)

        async def dispose() -> None:
            log.debug("AsyncMultiStream:dispose()")
            if observer in self._observers:
                self._observers.remove(observer)

        return AsyncDisposable.create(dispose)


# Alias
AsyncSubject = AsyncMultiSubject
