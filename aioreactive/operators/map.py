from typing import Awaitable, Callable, TypeVar

from aioreactive.core import Stream

from .transform import transform

TSource = TypeVar("TSource")
TResult = TypeVar("TResult")


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

    def handler(next: Callable[[TResult], Awaitable[None]], x: TSource):
        return next(mapper(x))

    return transform(handler)
