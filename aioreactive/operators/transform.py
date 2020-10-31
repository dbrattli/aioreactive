from typing import Awaitable, Callable, TypeVar

from aioreactive.core import AsyncAnonymousObservable, AsyncAnonymousObserver, AsyncObservable, AsyncObserver, Stream
from fslash.system import AsyncDisposable

TSource = TypeVar("TSource")
TResult = TypeVar("TResult")


def transform(
    anext: Callable[
        [
            Callable[
                [TResult],
                Awaitable[None],
            ],
            TSource,
        ],
        Awaitable[None],
    ]
) -> Stream[TSource, TResult]:
    def _(source: AsyncObservable[TSource]) -> AsyncObservable[TResult]:
        async def subscribe_async(aobv: AsyncObserver[TResult]) -> AsyncDisposable:
            async def asend(value: TResult) -> None:
                return await anext(aobv.asend, value)

            obv: AsyncObserver[TSource] = AsyncAnonymousObserver(asend, aobv.athrow, aobv.aclose)
            return await source.subscribe_async(obv)

        return AsyncAnonymousObservable(subscribe_async)

    return _
