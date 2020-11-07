from typing import Awaitable, Callable, TypeVar

from expression.collections import seq
from expression.core import compose
from expression.system import AsyncDisposable

from .combine import merge_inner, zip_seq
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


def starmap_async(amapper: Callable[..., Awaitable[TResult]]) -> Stream[TSource, TResult]:
    """Map async spreading arguments to the async mapper.

    Returns an observable sequence whose elements are the result of
    invoking the async mapper function on each element of the
    source."""

    async def handler(next: Callable[[TResult], Awaitable[None]], *args: TSource):
        b = await amapper(*args)
        return await next(b)

    return transform(handler)


def map(mapper: Callable[[TSource], TResult]) -> Stream[TSource, TResult]:
    """Map each element in the stream.

    Returns an observable sequence whose elements are the result of
    invoking the mapper function on each element of the source."""

    def handler(next: Callable[[TResult], Awaitable[None]], x: TSource) -> Awaitable[None]:
        return next(mapper(x))

    return transform(handler)


def starmap(mapper: Callable[..., TResult]) -> Stream[TSource, TResult]:
    """Map and spread the arguments to the mapper.

    Returns an observable sequence whose elements are the result of
    invoking the mapper function on each element of the source."""

    def handler(next: Callable[[TResult], Awaitable[None]], *args: TSource) -> Awaitable[None]:
        return next(mapper(*args))

    return transform(handler)


def mapi_async(mapper: Callable[[TSource, int], Awaitable[TResult]]) -> Stream[TSource, TResult]:
    """Map with index async.

    Returns an observable sequence whose elements are the result of
    invoking the async mapper function by incorporating the element's
    index on each element of the source.
    """
    return compose(zip_seq(seq.infinite()), starmap_async(mapper))


def mapi(mapper: Callable[[TSource, int], TResult]) -> Stream[TSource, TResult]:
    """Map with index.

    Returns an observable sequence whose elements are the result of
    invoking the mapper function and incorporating the element's index
    on each element of the source.
    """
    return compose(zip_seq(seq.infinite()), starmap(mapper))


def flat_map(mapper: Callable[[TSource], AsyncObservable[TResult]]) -> Stream[TSource, TResult]:
    """Flap map the observable sequence.

    Projects each element of an observable sequence into an observable
    sequence and merges the resulting observable sequences back into one
    observable sequence.

    Args:
        mapper: Function to transform each item in the stream.

    Returns:
        The result stream.
    """

    return compose(
        map(mapper),
        merge_inner(0),
    )


def flat_mapi(mapper: Callable[[TSource, int], AsyncObservable[TResult]]) -> Stream[TSource, TResult]:
    """Flat map with index.

    Projects each element of an observable sequence into an observable
    sequence by incorporating the element's index on each element of the
    source. Merges the resulting observable sequences back into one
    observable sequence.


    Args:
        mapper (Callable[[TSource, int], AsyncObservable[TResult]]): [description]

    Returns:
        Stream[TSource, TResult]: [description]
    """

    return compose(
        mapi(mapper),
        merge_inner(0),
    )


def flat_map_async(mapper: Callable[[TSource], Awaitable[AsyncObservable[TResult]]]) -> Stream[TSource, TResult]:
    """Flap map async.

    Asynchronously projects each element of an observable sequence into
    an observable sequence and merges the resulting observable sequences
    back into one observable sequence.


    Args:
        mapperCallable ([type]): [description]
        Awaitable ([type]): [description]

    Returns:
        Stream[TSource, TResult]: [description]
    """
    return compose(
        map_async(mapper),
        merge_inner(0),
    )


def flat_mapi_async(mapper: Callable[[TSource, int], Awaitable[AsyncObservable[TResult]]]) -> Stream[TSource, TResult]:
    """Flat map async with index.

    Asynchronously projects each element of an observable sequence into
    an observable sequence by incorporating the element's index on each
    element of the source. Merges the resulting observable sequences
    back into one observable sequence.

    Args:
        mapperAsync ([type]): [description]
        Awaitable ([type]): [description]

    Returns:
        Stream[TSource, TResult]: [description]
    """
    return compose(
        mapi_async(mapper),
        merge_inner(0),
    )


def concat_map(mapper: Callable[[TSource], AsyncObservable[TResult]]) -> Stream[TSource, TResult]:
    return compose(
        map(mapper),
        merge_inner(1),
    )
