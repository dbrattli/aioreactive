from typing import Tuple
import asyncio
import logging

from aioreactive.core import AsyncObservable, AsyncObserver
from aioreactive.core import chain, AsyncSingleStream
from aioreactive.core import AsyncCompositeDisposable, AsyncDisposable

log = logging.getLogger(__name__)


class Concat(AsyncObservable):

    def __init__(self, *operators: Tuple[AsyncObservable]) -> None:
        self._operators = iter(operators)
        self._subscription = None  # type: AsyncDisposable
        self._task = None  # type: asyncio.Task

    async def worker(self, observer: AsyncObserver) -> None:
        def recurse(fut) -> None:
            self._task = asyncio.ensure_future(self.worker(observer))

        try:
            source = next(self._operators)
        except StopIteration:
            await observer.aclose()
        except Exception as ex:
            await observer.athrow(ex)
        else:
            sink = Concat.Stream()
            down = await chain(sink, observer)  # type: AsyncDisposable
            sink.add_done_callback(recurse)
            up = await chain(source, sink)
            self._subscription = AsyncCompositeDisposable(up, down)

    async def __asubscribe__(self, observer: AsyncObserver) -> AsyncDisposable:
        async def cancel() -> None:
            if self._subscription is not None:
                await self._subscription.adispose()

            if self._task is not None:
                self._task.cancel()

        self._task = asyncio.ensure_future(self.worker(observer))
        return AsyncDisposable(cancel)

    class Stream(AsyncSingleStream):

        async def aclose_core(self) -> None:
            log.debug("Concat._:close()")
            self.cancel()


def concat(*operators: Tuple[AsyncObservable]) -> AsyncObservable:
    """Concatenate two source streams.

    Returns concatenated source stream.
    """
    return Concat(*operators)
