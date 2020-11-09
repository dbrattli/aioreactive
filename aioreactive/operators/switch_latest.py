import asyncio
import logging

from aioreactive.core import AsyncSingleStream
from aioreactive.core import AsyncObservable, AsyncObserver, chain

log = logging.getLogger(__name__)


class SwitchLatest(AsyncObservable):

    def __init__(self, source: AsyncObservable) -> None:
        self._source = source

    async def __asubscribe__(self, observer: AsyncObserver):
        _observer = await chain(SwitchLatest.Sink(self), observer)
        sub = await chain(self._source, _observer)
        sub.add_done_callback(_observer.done)
        return sub

    class Sink(AsyncSingleStream):

        def __init__(self, source: AsyncObservable) -> None:
            super().__init__()
            self._task = None  # type: asyncio.Task
            self._is_stopped = False
            self._latest = 0

        def done(self, sub=None) -> None:
            log.debug("SwitchLatest._:done()")
            if self._task:
                self._task.cancel()
                self._task = None
            self.latest = 0

        async def asend(self, stream) -> None:
            log.debug("SwitchLatest._:send(%s)", stream)
            inner_observer = await chain(SwitchLatest.Sink.Inner(self), self._observer)

            self._latest = id(inner_observer)
            inner_sub = await chain(stream, inner_observer)
            self._task = asyncio.ensure_future(inner_sub)

        async def aclose(self) -> None:
            log.debug("SwitchLatest._:close()")

            if not self._latest:
                self._is_stopped = True
                await self._observer.aclose()

        class Inner(AsyncSingleStream):

            def __init__(self, observer) -> None:
                super().__init__()
                self._parent = observer

            async def asend(self, value) -> None:
                if self._parent._latest == id(self):
                    await self._observer.asend(value)

            async def athrow(self, error: Exception):
                if self._parent._latest == id(self):
                    await self._observer.athrow(error)

            async def aclose(self) -> None:
                if self._parent._latest == id(self):
                    if self._parent._is_stopped:
                        await self._observer.aclose()


def switch_latest(source: AsyncObservable) -> AsyncObservable:
    """Switch to the latest source stream.

    Flattens a source stream of source streams into a source stream
    that only produces values from the most recent source stream.

    Returns a flattened source stream.
    """
    return SwitchLatest(source)
