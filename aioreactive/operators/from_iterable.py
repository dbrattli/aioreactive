from typing import Generic, TypeVar, Iterable
import asyncio
import logging

from aioreactive.core import AsyncObserver, AsyncObservable
from aioreactive.core import AsyncSingleStream, AsyncDisposable

log = logging.getLogger(__name__)
T = TypeVar('T')


class FromIterable(AsyncObservable, Generic[T]):

    def __init__(self, iterable) -> None:
        assert hasattr(iterable, "__iter__")
        self.iterable = iterable

    async def __asubscribe__(self, observer: AsyncObserver) -> AsyncDisposable:
        task = None

        assert isinstance(observer, AsyncObserver)

        async def cancel():
            task.cancel()

        sub = AsyncDisposable(cancel)

        async def worker() -> None:
            log.debug("sync_worker()")
            for value in self.iterable:
                try:
                    log.debug("sync_worker. asending: %s", value)
                    await observer.asend(value)
                except Exception as ex:
                    await observer.athrow(ex)
                    return

            await observer.aclose()

        try:
            task = asyncio.ensure_future(worker())
        except Exception as ex:
            log.debug("FromIterable:worker(), Exception: %s" % ex)
            await observer.athrow(ex)
        return sub


def from_iterable(iterable: Iterable[T]) -> AsyncObservable[T]:
    """Convert an iterable to a source stream.

    1 - xs = from_iterable([1,2,3])

    Returns the source stream whose elements are pulled from the
    given (async) iterable sequence."""

    return FromIterable(iterable)
