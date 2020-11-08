from typing import Awaitable, Callable, TypeVar

from expression.core import Option, aio

from .transform import transform
from .types import Stream

TSource = TypeVar("TSource")
TResult = TypeVar("TResult")


def choose_async(chooser: Callable[[TSource], Awaitable[Option[TResult]]]) -> Stream[TSource, TResult]:
    """Choose async.

    Applies the given async function to each element of the stream and
    returns the stream comprised of the results for each element where
    the function returns Some with some value.

    Args:
        chooser (Callable[[TSource], Awaitable[Option[TResult]]]): [description]

    Returns:
        Stream[TSource, TResult]: [description]
    """

    async def handler(next: Callable[[TResult], Awaitable[None]], xs: TSource) -> None:
        result = await chooser(xs)
        for x in result.to_list():
            await next(x)

    return transform(handler)


def choose(chooser: Callable[[TSource], Option[TResult]]) -> Stream[TSource, TResult]:
    """Choose.

    Applies the given function to each element of the stream and returns
    the stream comprised of the results for each element where the
    function returns Some with some value.

    Args:
        chooser (Callable[[TSource], Option[TResult]]): [description]

    Returns:
        Stream[TSource, TResult]: [description]
    """

    def handler(next: Callable[[TResult], Awaitable[None]], xs: TSource) -> Awaitable[None]:
        for x in chooser(xs).to_list():
            return next(x)
        return aio.empty

    return transform(handler)


def filter_async(predicate: Callable[[TSource], Awaitable[bool]]) -> Stream[TSource, TSource]:
    """Filter async.

    Filters the elements of an observable sequence based on an async
    predicate. Returns an observable sequence that contains elements
    from the input sequence that satisfy the condition.

    Args:
        predicate (Callable[[TSource], Awaitable[bool]]): [description]

    Returns:
        Stream[TSource, TSource]: [description]
    """

    async def handler(next: Callable[[TResult], Awaitable[None]], x: TSource):
        if predicate(x):
            return await next(x)

    return transform(handler)


def filter(predicate: Callable[[TSource], bool]) -> Stream[TSource, TSource]:
    """Filter stream.

    Filters the elements of an observable sequence based on a predicate.
    Returns an observable sequence that contains elements from the input
    sequence that satisfy the condition.


    Args:
        predicate (Callable[[TSource], bool]): [description]

    Returns:
        Stream[TSource, TSource]: [description]
    """

    def handler(next: Callable[[TResult], Awaitable[None]], x: TSource) -> Awaitable[None]:
        if predicate(x):
            return next(x)
        return aio.empty

    return transform(handler)
