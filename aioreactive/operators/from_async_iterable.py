from typing import Generic, TypeVar, AsyncIterable
import asyncio
import logging

from aioreactive.core import AsyncObserver, AsyncObservable
from aioreactive.core import AsyncDisposable

log = logging.getLogger(__name__)
T = TypeVar('T')


class FromAsyncIterable(AsyncObservable, Generic[T]):

    def __init__(self, iterable) -> None:
        assert hasattr(iterable, "__aiter__")
        self.iterable = iterable

    async def __asubscribe__(self, observer: AsyncObserver) -> AsyncDisposable:
        task = None

        assert isinstance(observer, AsyncObserver)

        async def cancel():
            task.cancel()

        sub = AsyncDisposable(cancel)

        async def worker() -> None:
            async for value in self.iterable:
                try:
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


def from_async_iterable(iterable: AsyncIterable[T]) -> AsyncObservable[T]:
    """Convert an async iterable to a source stream.

    2 - xs = from_async_iterable(async_iterable)

    Returns the source stream whose elements are pulled from the
    given (async) iterable sequence."""

    return FromAsyncIterable(iterable)
