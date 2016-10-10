import logging
from asyncio import Future
from typing import TypeVar, Generic, Dict

from .typing import AsyncSink
from .futures import Subscription

log = logging.getLogger(__name__)

T = TypeVar("T")


class Stream(AsyncSink, Generic[T]):
    """The Stream.

    The stream is both a source and a sink. Thus you can both listen
    to it and send values to it. Any values send will be forwarded to
    all listeners.
    """

    def __init__(self) -> None:
        self._sinks = {}  # type: Dict[AsyncSink, Subscription]

    async def send(self, value: T) -> None:
        for sink, sub in list(self._sinks.items()):
            await sink.send(value)

    async def throw(self, ex: Exception) -> None:
        for sink, sub in list(self._sinks.items()):
            await sink.throw(ex)
            sub.set_exception(ex)

    async def close(self) -> None:
        for sink, sub in list(self._sinks.items()):
            await sink.close()

    async def __alisten__(self, sink: AsyncSink):
        sub = Subscription()
        self._sinks[sink] = sub

        def done(sub: Future) -> None:
            log.debug("Stream:done()")
            if sink in self._sinks:
                del self._sinks[sink]

        sub.add_done_callback(done)
        return sub
