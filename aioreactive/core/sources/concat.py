from typing import Tuple
import asyncio
import logging

from aioreactive.core import AsyncSource, AsyncSink
from aioreactive.core import chain, AsyncSingleStream

log = logging.getLogger(__name__)


class Concat(AsyncSource):

    def __init__(self, *sources: Tuple[AsyncSource]) -> None:
        self._sources = iter(sources)
        self._subscription = None  # type: asyncio.Future
        self._task = None  # type: asyncio.Task

    async def worker(self, sink: AsyncSink) -> None:
        def recurse(fut) -> None:
            self._task = asyncio.ensure_future(self.worker(sink))

        try:
            source = next(self._sources)
        except StopIteration:
            await sink.aclose()
        except Exception as ex:
            await sink.athrow(ex)
        else:
            _sink = await chain(Concat.Stream(), sink)  # type: AsyncSingleStream
            _sink.add_done_callback(recurse)

            self._subscription = await chain(source, _sink)

    async def __astart__(self, sink: AsyncSink) -> AsyncSingleStream:
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


def concat(other: AsyncSource, source: AsyncSource) -> AsyncSource:
    """Concatenate two source streams.

    Returns concatenated source stream.
    """
    return Concat(source, other)
