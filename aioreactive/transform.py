from typing import Awaitable, Callable, TypeVar

from fslash.system import AsyncDisposable

from .observables import AsyncAnonymousObservable, AsyncObservable
from .observers import AsyncAnonymousObserver
from .types import AsyncObserver, Stream

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
            print("transform:subscribe_async")

            async def asend(value: TResult) -> None:
                return await anext(aobv.asend, value)

            obv: AsyncObserver[TSource] = AsyncAnonymousObserver(asend, aobv.athrow, aobv.aclose)
            sub = await source.subscribe_async(obv)
            print(sub)
            return sub

        return AsyncAnonymousObservable(subscribe_async)

    return _


def map_async(amapper: Callable[[TSource], Awaitable[TResult]]) -> Stream[TSource, TResult]:
    """Returns an observable sequence whose elements are the result of
    invoking the async mapper function on each element of the
    source."""

    async def handler(next: Callable[[TResult], Awaitable[None]], x: TSource):
        b = await amapper(x)
        return await next(b)

    return transform(handler)


def map(mapper: Callable[[TSource], TResult]) -> Stream[TSource, TResult]:
    """Returns an observable sequence whose elements are the result of
    invoking the mapper function on each element of the source."""

    def handler(next: Callable[[TResult], Awaitable[None]], x: TSource) -> Awaitable[None]:
        return next(mapper(x))

    return transform(handler)
