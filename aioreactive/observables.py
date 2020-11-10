import logging
from typing import Awaitable, Callable, TypeVar

from expression.system import AsyncDisposable

from .types import AsyncObservable, AsyncObserver

TSource = TypeVar("TSource")
TResult = TypeVar("TResult")
TOther = TypeVar("TOther")
TError = TypeVar("TError")
T1 = TypeVar("T1")
T2 = TypeVar("T2")

log = logging.getLogger(__name__)


class AsyncAnonymousObservable(AsyncObservable[TSource]):

    """An AsyncObservable that works with Python special methods.

    This class supports python special methods including pipe-forward
    using OR operator. All operators are provided as partially applied
    plain old functions
    """

    def __init__(self, subscribe: Callable[[AsyncObserver[TSource]], Awaitable[AsyncDisposable]]) -> None:
        self._subscribe = subscribe

    async def subscribe_async(self, observer: AsyncObserver[TSource]) -> AsyncDisposable:
        log.debug("AsyncAnonymousObservable:subscribe_async(%s)", self._subscribe)
        return await self._subscribe(observer)
