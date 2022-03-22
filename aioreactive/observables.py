import logging
from typing import AsyncIterable, AsyncIterator, Awaitable, Callable, TypeVar

from expression.system import AsyncDisposable

from .observers import AsyncIteratorObserver
from .types import AsyncObservable, AsyncObserver

_TSource = TypeVar("_TSource")
_TResult = TypeVar("_TResult")
_TOther = TypeVar("_TOther")
_TError = TypeVar("_TError")
_T1 = TypeVar("_T1")
_T2 = TypeVar("_T2")

log = logging.getLogger(__name__)


class AsyncAnonymousObservable(AsyncObservable[_TSource]):

    """An anonymous AsyncObservable.

    Uses a custom subscribe method.
    """

    def __init__(
        self, subscribe: Callable[[AsyncObserver[_TSource]], Awaitable[AsyncDisposable]]
    ) -> None:
        self._subscribe = subscribe

    async def subscribe_async(
        self, observer: AsyncObserver[_TSource]
    ) -> AsyncDisposable:
        log.debug("AsyncAnonymousObservable:subscribe_async(%s)", self._subscribe)
        return await self._subscribe(observer)


class AsyncIterableObservable(AsyncIterable[_TSource], AsyncObservable[_TSource]):
    def __init__(self, source: AsyncObservable[_TSource]) -> None:
        self._source = source

    async def subscribe_async(
        self, observer: AsyncObserver[_TSource]
    ) -> AsyncDisposable:
        return await self._source.subscribe_async(observer)

    def __aiter__(self) -> AsyncIterator[_TSource]:
        """Iterate asynchronously.

        Transforms the async source to an async iterable. The source
        will await for the iterator to pick up the value before
        continuing to avoid queuing values.

        Returns:
            An async iterator.
        """

        return AsyncIteratorObserver(self)
