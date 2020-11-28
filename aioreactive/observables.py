import logging
from typing import AsyncIterable, AsyncIterator, Awaitable, Callable, TypeVar

from expression.system import AsyncDisposable

from .observers import AsyncIteratorObserver
from .types import AsyncObservable, AsyncObserver

TSource = TypeVar("TSource")
TResult = TypeVar("TResult")
TOther = TypeVar("TOther")
TError = TypeVar("TError")
T1 = TypeVar("T1")
T2 = TypeVar("T2")

log = logging.getLogger(__name__)


class AsyncAnonymousObservable(AsyncObservable[TSource]):

    """An anonymous AsyncObservable.

    Uses a custom subscribe method.
    """

    def __init__(self, subscribe: Callable[[AsyncObserver[TSource]], Awaitable[AsyncDisposable]]) -> None:
        self._subscribe = subscribe

    async def subscribe_async(self, observer: AsyncObserver[TSource]) -> AsyncDisposable:
        log.debug("AsyncAnonymousObservable:subscribe_async(%s)", self._subscribe)
        return await self._subscribe(observer)


class AsyncIterableObservable(AsyncIterable[TSource], AsyncObservable[TSource]):
    def __init__(self, source: AsyncObservable[TSource]) -> None:
        self._source = source

    async def subscribe_async(self, observer: AsyncObserver[TSource]) -> AsyncDisposable:
        return await self._source.subscribe_async(observer)

    def __aiter__(self) -> AsyncIterator[TSource]:
        """Iterate asynchronously.

        Transforms the async source to an async iterable. The source
        will await for the iterator to pick up the value before
        continuing to avoid queuing values.

        Returns:
            An async iterator.
        """

        return AsyncIteratorObserver(self)
