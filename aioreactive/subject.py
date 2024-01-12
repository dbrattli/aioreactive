import logging
from asyncio import Future
from typing import TypeVar

from expression.system import AsyncDisposable, ObjectDisposedException

from .observables import AsyncAnonymousObserver, AsyncObservable
from .types import AsyncObserver, CloseAsync, SendAsync, ThrowAsync


log = logging.getLogger(__name__)

_TSource = TypeVar("_TSource")


class AsyncSingleSubject(AsyncObserver[_TSource], AsyncObservable[_TSource], AsyncDisposable):
    """An stream with a single sink.

    Both an async observable and async observer.

    The `AsyncSingleStream` is cold in the sense that it will await an
    observer before forwarding any events.
    """

    def __init__(self) -> None:
        super().__init__()

        self._wait: Future[bool] = Future()
        self._observer: AsyncObserver[_TSource] | None = None
        self._is_disposed = False
        self._is_stopped = False

    def check_disposed(self) -> None:
        if self._is_disposed:
            raise ObjectDisposedException()

    async def asend(self, value: _TSource) -> None:
        log.debug("AsyncSingleStream:asend(%s)", str(value))

        self.check_disposed()

        # AsyncSingleStreams are cold and will await a sink.
        while self._observer is None:
            log.debug("AsyncSingleStream:asend:awaiting start")
            await self._wait
            log.debug("AsyncSingleStream:asend:awaiting:done")

        if not self._is_stopped:
            await self._observer.asend(value)

    async def athrow(self, error: Exception) -> None:
        log.debug("AsyncSingleStream:athrow()")

        while self._observer is None:
            await self._wait

        self.check_disposed()
        if not self._is_stopped:
            await self._observer.athrow(error)
            self._is_stopped = True

    async def aclose(self) -> None:
        log.debug("AsyncSingleStream:aclose()")

        while self._observer is None:
            log.debug("AsyncSingleStream:aclose:awaiting start")
            await self._wait

        self.check_disposed()
        if not self._is_stopped:
            log.debug("AsyncSingleStream:subscription disposed")
            await self._observer.aclose()
            self._is_stopped = True

    async def dispose_async(self) -> None:
        log.debug("AsyncSingleStream:dispose_async()")

        self._observer = None
        self._is_disposed = True

    async def subscribe_async(
        self,
        send: SendAsync[_TSource] | AsyncObserver[_TSource] | None = None,
        throw: ThrowAsync | None = None,
        close: CloseAsync | None = None,
    ) -> AsyncDisposable:
        """Start streaming."""
        self.check_disposed()
        self._observer = send if isinstance(send, AsyncObserver) else AsyncAnonymousObserver(send, throw, close)

        if not self._wait.done():
            self._wait.set_result(True)

        return AsyncDisposable.create(self.dispose_async)


class AsyncMultiSubject(AsyncObserver[_TSource], AsyncObservable[_TSource], AsyncDisposable):
    """An stream with a multiple observers.

    Both an async observable and async observer.

    The AsyncMultiStream is "hot" in the sense that it will drop events
    if there are currently no subscribed observers.
    """

    def __init__(self) -> None:
        super().__init__()
        self._observers: list[AsyncObserver[_TSource]] = []
        self._is_disposed = False
        self._is_stopped = False

    def check_disposed(self) -> None:
        if self._is_disposed:
            raise ObjectDisposedException()

    async def asend(self, value: _TSource) -> None:
        self.check_disposed()

        if self._is_stopped:
            return

        for obv in list(self._observers):
            await obv.asend(value)

    async def athrow(self, error: Exception) -> None:
        self.check_disposed()

        if self._is_stopped:
            return
        self._is_stopped = True

        for obv in list(self._observers):
            await obv.athrow(error)

    async def aclose(self) -> None:
        self.check_disposed()

        if self._is_stopped:
            return
        self._is_stopped = True

        for obv in list(self._observers):
            await obv.aclose()

    async def subscribe_async(
        self,
        send: SendAsync[_TSource] | AsyncObserver[_TSource] | None = None,
        throw: ThrowAsync | None = None,
        close: CloseAsync | None = None,
    ) -> AsyncDisposable:
        """Subscribe."""
        log.debug("AsyncMultiStream:subscribe_async()")
        self.check_disposed()

        observer = send if isinstance(send, AsyncObserver) else AsyncAnonymousObserver(send, throw, close)
        self._observers.append(observer)

        async def dispose() -> None:
            log.debug("AsyncMultiStream:dispose()")
            if observer in self._observers:
                self._observers.remove(observer)

        return AsyncDisposable.create(dispose)

    async def dispose_async(self) -> None:
        self._is_disposed = True


# Alias
AsyncSubject = AsyncMultiSubject
