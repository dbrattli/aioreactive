from typing import Generic, TypeVar, Iterable
import asyncio
import logging

from aioreactive.abc import AsyncDisposable
from aioreactive.core import AsyncObserver, AsyncObservable
from aioreactive.core import AsyncSingleStream, chain

log = logging.getLogger(__name__)
T = TypeVar('T')


class CatchException(AsyncObservable[T], Generic[T]):

    def __init__(self, iterable) -> None:
        self.iterable = iterable

    async def __asubscribe__(self, observer: AsyncObserver) -> AsyncDisposable:
        iterator = iter(self.iterable)
        current = None
        task = None

        def cancel(sub):
            asyncio.ensure_future(worker())

        async def worker() -> None:
            nonlocal current

            sub = CatchException.Stream(worker)
            sub.add_done_callback(cancel)

            try:
                current = next(iterator)
            except StopIteration:
                await sub.aclose()

            _observer = await chain(sub, observer)
            await chain(self._source, _observer)

        task = asyncio.ensure_future(worker())
        return sub

    class Stream(AsyncSingleStream, Generic[T]):

        def __init__(self, source: "CatchException", worker) -> None:
            super().__init__()
            self.worker = worker

        async def athrow(self, ex: Exception) -> None:
            self.cancel()


def catch_exception(iterable: Iterable[T]) -> AsyncObservable[T]:

    return CatchException(iterable)
