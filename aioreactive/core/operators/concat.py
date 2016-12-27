from typing import Tuple
import asyncio
import logging

from aioreactive.core import AsyncObservable, AsyncObserver
from aioreactive.core import chain, AsyncSingleStream

log = logging.getLogger(__name__)


class Concat(AsyncObservable):

    def __init__(self, *operators: Tuple[AsyncObservable]) -> None:
        self._operators = iter(operators)
        self._subscription = None  # type: asyncio.Future
        self._task = None  # type: asyncio.Task

    async def worker(self, sink: AsyncObserver) -> None:
        def recurse(fut) -> None:
            self._task = asyncio.ensure_future(self.worker(sink))

        try:
            source = next(self._operators)
        except StopIteration:
            await sink.aclose()
        except Exception as ex:
            await sink.athrow(ex)
        else:
            _observer = await chain(Concat.Stream(), sink)  # type: AsyncSingleStream
            _observer.add_done_callback(recurse)

            self._subscription = await chain(source, _observer)

    async def __asubscribe__(self, sink: AsyncObserver) -> AsyncSingleStream:
        stream = AsyncSingleStream()

        def cancel(sub):
            if self._subscription is not None:
                self._subscription.cancel()

            if self._task is not None:
                self._task.cancel()
        stream.add_done_callback(cancel)

        self._task = asyncio.ensure_future(self.worker(sink))
        return stream

    class Stream(AsyncSingleStream):

        async def aclose(self) -> None:
            log.debug("Concat._:close()")
            self.cancel()


def concat(*operators: Tuple[AsyncObservable]) -> AsyncObservable:
    """Concatenate two source streams.

    Returns concatenated source stream.
    """
    return Concat(*operators)
