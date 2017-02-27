from typing import Generic, TypeVar, Iterable
import asyncio
import logging

from aioreactive.core import AsyncObserver, AsyncObservable
from aioreactive.core import AsyncSingleStream, AsyncDisposable

log = logging.getLogger(__name__)
T = TypeVar('T')


class FromIterable(AsyncObservable, Generic[T]):

    def __init__(self, iterable) -> None:
        self.iterable = iterable

    async def __asubscribe__(self, observer: AsyncObserver) -> AsyncDisposable:
        task = None

        async def cancel():
            task.cancel()

        sub = AsyncDisposable(cancel)

        async def async_worker() -> None:
            async for value in self.iterable:
                try:
                    await observer.asend(value)
                except Exception as ex:
                    await observer.athrow(ex)
                    return

            await observer.aclose()

        async def sync_worker() -> None:
            log.debug("sync_worker()")
            for value in self.iterable:
                try:
                    log.debug("sync_worker. asending: %s" % value)
                    await observer.asend(value)
                except Exception as ex:
                    await observer.athrow(ex)
                    return

            await observer.aclose()

        if hasattr(self.iterable, "__aiter__"):
            worker = async_worker
        elif hasattr(self.iterable, "__iter__"):
            worker = sync_worker
        else:
            raise ValueError("Argument must be iterable or async iterable.")

        try:
            task = asyncio.ensure_future(worker())
        except Exception as ex:
            log.debug("FromIterable:worker(), Exception: %s" % ex)
            await observer.athrow(ex)
        return sub


def from_iterable(iterable: Iterable[T]) -> AsyncObservable[T]:
    """Convert an (async) iterable to a source stream.

    1 - xs = from_iterable([1,2,3])
    2 - xs = from_iterable(async_iterable)

    Returns the source stream whose elements are pulled from the
    given (async) iterable sequence."""

    return FromIterable(iterable)
