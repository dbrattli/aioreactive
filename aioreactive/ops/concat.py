import asyncio
from asyncio import Future
import logging

from aioreactive.core.futures import AsyncMultiFuture
from aioreactive.abc import AsyncSource, AsyncSink
from aioreactive.core import chain, Subscription

log = logging.getLogger(__name__)


class Concat(AsyncSource):
    def __init__(self, *sources):
        self._sources = iter(sources)
        self._subscription = None
        self._task = None

    async def worker(self, sink: AsyncSink):
        def recurse(fut):
            self._task = asyncio.ensure_future(self.worker(sink))

        try:
            source = next(self._sources)
        except StopIteration:
            await sink.close()
        except Exception as ex:
            await sink.throw(ex)
        else:
            _sink = await chain(Concat.Sink(), sink)
            _sink.add_done_callback(recurse)

            self._subscription = await chain(source, _sink)

    async def __alisten__(self, sink: AsyncSink):
        def cancel(sub):
            if self._subscription is not None:
                self._subscription.cancel()

            if self._task is not None:
                self._task.cancel()

        self._task = asyncio.ensure_future(self.worker(sink))
        return Subscription(cancel)

    class Sink(AsyncMultiFuture):
        async def close(self):
            log.debug("Concat._:close()")
            self.cancel()


def concat(other: AsyncSource, source: AsyncSource) -> AsyncSource:
    """Concatenate two source streams.

    Returns concatenated source stream.
    """
    return Concat(source, other)
