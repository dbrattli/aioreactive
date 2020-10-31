import asyncio
import logging
from typing import AsyncIterable, Generic, TypeVar

from aioreactive.core import AsyncObservable, AsyncObserver
from fslash.system import AsyncDisposable

log = logging.getLogger(__name__)
TSource = TypeVar("TSource")


class FromAsyncIterable(AsyncObservable, Generic[TSource]):
    def __init__(self, iterable) -> None:
        assert hasattr(iterable, "__aiter__")
        self.iterable = iterable

    async def __asubscribe__(self, observer: AsyncObserver) -> AsyncDisposable:
        task = None

        assert isinstance(observer, AsyncObserver)

        async def cancel():
            task.cancel()

        sub = AsyncDisposable.create(cancel)

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


def from_async_iterable(iterable: AsyncIterable[TSource]) -> AsyncObservable[TSource]:
    """Convert an async iterable to a source stream.

    2 - xs = from_async_iterable(async_iterable)

    Returns the source stream whose elements are pulled from the
    given (async) iterable sequence."""

    return FromAsyncIterable(iterable)
