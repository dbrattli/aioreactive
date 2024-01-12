import asyncio
from collections.abc import AsyncIterable, Iterable
from typing import TypeVar

import reactivex
from expression.system.disposable import AsyncDisposable
from reactivex import Observable
from reactivex.abc import DisposableBase, ObserverBase, SchedulerBase
from reactivex.disposable import Disposable

from .observables import AsyncAnonymousObserver, AsyncIterableObservable, AsyncObservable


_TSource = TypeVar("_TSource")


def to_async_iterable(source: AsyncObservable[_TSource]) -> AsyncIterable[_TSource]:
    """Convert async observable to async iterable.

    Args:
        source: The source observable.
        count: The number of elements to skip before returning the
            remaining values.

    Returns:
        A source stream that contains the values that occur
        after the specified index in the input source stream.
    """
    return AsyncIterableObservable(source)


def to_observable(source: AsyncObservable[_TSource]) -> Observable[_TSource]:
    """Convert async observable to observable."""

    def subscribe(obv: ObserverBase[_TSource], scheduler: Optional[SchedulerBase] = None) -> DisposableBase:
        subscription: Optional[AsyncDisposable] = None

        async def start() -> None:
            nonlocal subscription

            async def asend(value: _TSource) -> None:
                obv.on_next(value)

            async def athrow(error: Exception) -> None:
                obv.on_error(error)

            async def aclose() -> None:
                obv.on_completed()

            subscription = await source.subscribe_async(AsyncAnonymousObserver(asend, athrow, aclose))

        asyncio.create_task(start())

        def dispose() -> None:
            if subscription:
                asyncio.create_task(subscription.dispose_async())

        return Disposable(dispose)

    return reactivex.create(subscribe)


def to_iterable(source: AsyncObservable[_TSource]) -> Iterable[_TSource]:
    """Convert async observable to iterable."""
    return to_observable(source).to_iterable()
