import logging
from collections.abc import AsyncIterable, AsyncIterator, Awaitable, Callable
from typing import TypeVar

from expression.system import AsyncDisposable

from .observers import AsyncAnonymousObserver, AsyncIteratorObserver
from .types import AsyncObservable, AsyncObserver, CloseAsync, SendAsync, ThrowAsync


_TSource = TypeVar("_TSource")

log = logging.getLogger(__name__)


class AsyncAnonymousObservable(AsyncObservable[_TSource]):
    """An anonymous AsyncObservable.

    Uses a custom subscribe method.
    """

    def __init__(self, subscribe: Callable[[AsyncObserver[_TSource]], Awaitable[AsyncDisposable]]) -> None:
        self._subscribe = subscribe

    async def subscribe_async(
        self,
        send: SendAsync[_TSource] | AsyncObserver[_TSource] | None = None,
        throw: ThrowAsync | None = None,
        close: CloseAsync | None = None,
    ) -> AsyncDisposable:
        observer = send if isinstance(send, AsyncObserver) else AsyncAnonymousObserver(send, throw, close)
        log.debug("AsyncAnonymousObservable:subscribe_async(%s)", self._subscribe)
        return await self._subscribe(observer)


class AsyncIterableObservable(AsyncIterable[_TSource], AsyncObservable[_TSource]):
    def __init__(self, source: AsyncObservable[_TSource]) -> None:
        self._source = source

    async def subscribe_async(
        self,
        send: SendAsync[_TSource] | AsyncObserver[_TSource] | None = None,
        throw: ThrowAsync | None = None,
        close: CloseAsync | None = None,
    ) -> AsyncDisposable:
        observer = send if isinstance(send, AsyncObserver) else AsyncAnonymousObserver(send, throw, close)
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


__all__ = ["AsyncAnonymousObservable", "AsyncIterableObservable"]
