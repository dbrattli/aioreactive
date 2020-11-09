import asyncio
from asyncio.locks import BoundedSemaphore
from typing import Dict, TypeVar
import logging

from aioreactive.core.utils import noopobserver
from aioreactive.core import AsyncSingleStream, AsyncDisposable, AsyncCompositeDisposable
from aioreactive.core import AsyncObservable, AsyncObserver, chain

T = TypeVar('T')
log = logging.getLogger(__name__)


class Merge(AsyncObservable):

    def __init__(self, source: AsyncObservable, max_concurrent: int) -> None:
        self._source = source
        self.max_concurrent = max_concurrent

    async def __asubscribe__(self, observer: AsyncObserver) -> AsyncDisposable:
        log.debug("Merge:__asubscribe__()")
        sink = Merge.Sink(self, self.max_concurrent)
        down = await chain(sink, observer)
        up = await chain(self._source, sink)

        return AsyncCompositeDisposable(up, down)

    class Sink(AsyncSingleStream):

        def __init__(self, source: AsyncObservable, max_concurrent: int) -> None:
            super().__init__()
            self._inner_subs = {}  # type: Dict[AsyncObserver[T], AsyncSingleStream]
            self._sem = BoundedSemaphore(max_concurrent)
            self._is_closed = False

        async def cancel(self, sub=None) -> None:
            log.debug("Merge.Sink:adispose()")
            super().cancel()

            # Use .values() so that no one modifies the dict while we
            # cancel the inner streams.
            for sub in self._inner_subs.values():
                if sub is not None:
                    await sub.adispose()
            self._inner_subs = {}

        async def asend_core(self, stream: AsyncObservable) -> None:
            log.debug("Merge.Sink:asend_core(%s)", stream)

            inner_stream = Merge.Sink.InnerStream()
            inner_sub = await chain(inner_stream, self._observer)  # type: AsyncDisposable

            # Allocate entry to make sure no-one closes the merge before
            # we get to aquire the semaphore.
            self._inner_subs[inner_sub] = None
            await self._sem.acquire()

            def done(sub):
                self._inner_subs.pop(inner_sub, None)
                self._sem.release()

                if self._is_closed and not len(self._inner_subs):
                    asyncio.ensure_future(self._observer.aclose())

            inner_stream.add_done_callback(done)
            sub = self._inner_subs[inner_sub] = await chain(stream, inner_stream)
            return sub

        async def aclose_core(self) -> None:
            log.debug("Merge.Sink:aclose_core()")

            if len(self._inner_subs):
                self._is_closed = True
                return

            log.debug("Closing merge ...")
            await self._observer.aclose()

        class InnerStream(AsyncSingleStream):

            async def aclose_core(self) -> None:
                log.debug("Merge.Sink.InnerStream:aclose()")

                # Unlink observer to avoid forwarding the close. This will
                # make the inner_stream complete, and the done callback
                # will take care of any cleanup.
                self._observer = noopobserver


def merge(source: AsyncObservable, max_concurrent: int=42) -> AsyncObservable:
    """Merges a source stream of source streams.

    Keyword arguments:
    source -- source stream to merge.
    max_concurrent -- Max number of streams to process concurrently.
        Default value is 42. Setting this to 1 turns merge into concat.

    Returns flattened source stream.
    """
    return Merge(source, max_concurrent)
