from typing import Awaitable, Callable, List, TypeVar

from expression.core import Option, Result, aio, match, pipe
from expression.core.fn import TailCall, recursive_async
from expression.core.mailbox import MailboxProcessor
from expression.system.disposable import AsyncDisposable

from .notification import Notification, OnCompleted, OnError, OnNext
from .observables import AsyncAnonymousObservable
from .observers import AsyncAnonymousObserver, AsyncNotificationObserver, auto_detach_observer
from .transform import transform
from .types import AsyncObservable, AsyncObserver, Stream

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

    async def handler(next: Callable[[TSource], Awaitable[None]], x: TSource):
        print("handler: ", x)
        if await predicate(x):
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

    def handler(next: Callable[[TSource], Awaitable[None]], x: TSource) -> Awaitable[None]:
        if predicate(x):
            return next(x)
        return aio.empty

    return transform(handler)


def distinct_until_changed(source: AsyncObservable[TSource]) -> AsyncObservable[TSource]:
    """Distinct until changed.

    Return an observable sequence only containing the distinct
    contiguous elementsfrom the source sequence.

    Args:
        source (AsyncObservable[TSource]): [description]

    Returns:
        AsyncObservable[TSource]: [description]
    """

    async def subscribe_async(aobv: AsyncObserver[TSource]) -> AsyncDisposable:
        safe_obv, auto_detach = auto_detach_observer(aobv)

        async def worker(inbox: MailboxProcessor[Notification[TSource]]) -> None:
            @recursive_async
            async def message_loop(latest: Notification[TSource]) -> Result[Notification[TSource], Exception]:
                n = await inbox.receive()

                async def get_latest() -> Notification[TSource]:
                    with match(n) as m:
                        for x in m.case(OnNext):
                            if n == latest:
                                break
                            try:
                                await safe_obv.asend(x)
                            except Exception as ex:
                                await safe_obv.athrow(ex)
                            break
                        for err in m.case(OnError):
                            await safe_obv.athrow(err)
                            break
                        while m.case(OnCompleted):
                            await safe_obv.aclose()
                            break

                    return n

                latest = await get_latest()
                return TailCall(latest)

            await message_loop(OnCompleted)  # Use as sentinel value as it will not match any OnNext value

        agent = MailboxProcessor.start(worker)

        async def notification(n: Notification[TSource]) -> None:
            agent.post(n)

        obv: AsyncObserver[TSource] = AsyncNotificationObserver(notification)
        return await pipe(obv, source.subscribe_async, auto_detach)

    return AsyncAnonymousObservable(subscribe_async)


def skip(count: int) -> Stream[TSource, TSource]:
    """[summary]

    Bypasses a specified number of elements in an observable sequence
    and then returns the remaining elements.

    Args:
        count (int): [description]

    Returns:
        Stream[TSource, TSource]: [description]
    """

    def _skip(source: AsyncObservable[TSource]) -> AsyncObservable[TSource]:
        async def subscribe_async(obvAsync: AsyncObserver[TSource]) -> AsyncDisposable:
            safe_obv, auto_detach = auto_detach_observer(obvAsync)

            remaining = count

            async def asend(value: TSource) -> None:
                nonlocal remaining
                if remaining <= 0:
                    await safe_obv.asend(value)
                else:
                    remaining -= 1

            async def athrow(ex: Exception) -> None:
                await safe_obv.athrow(ex)

            async def aclose() -> None:
                await safe_obv.aclose()

            obv = AsyncAnonymousObserver(asend, athrow, aclose)
            return await pipe(obv, source.subscribe_async, auto_detach)

        return AsyncAnonymousObservable(subscribe_async)

    return _skip


def take(count: int) -> Stream[TSource, TSource]:
    """Take the first elements from the stream.

    Returns a specified number of contiguous elements from the start of
    an observable sequence.

    Args:
        count Number of elements to take.

    Returns:
        Stream[TSource, TSource]: [description]
    """

    def _take(source: AsyncObservable[TSource]) -> AsyncObservable[TSource]:
        async def subscribe_async(obvAsync: AsyncObserver[TSource]) -> AsyncDisposable:
            safe_obv, auto_detach = auto_detach_observer(obvAsync)

            remaining = count

            async def asend(value: TSource) -> None:
                nonlocal remaining

                if remaining > 0:
                    remaining -= 1
                    await safe_obv.asend(value)
                    if not remaining:
                        await safe_obv.aclose()

            async def athrow(ex: Exception) -> None:
                await safe_obv.athrow(ex)

            async def aclose() -> None:
                await safe_obv.aclose()

            obv = AsyncAnonymousObserver(asend, athrow, aclose)
            return await pipe(obv, source.subscribe_async, auto_detach)

        return AsyncAnonymousObservable(subscribe_async)

    return _take


def take_last(count: int) -> Stream[TSource, TSource]:
    """Take last elements from stream.

    Returns a specified number of contiguous elements from the end of an
    observable sequence.

    Args:
        count: Number of elements to take.

    Returns:
        Stream[TSource, TSource]: [description]
    """

    def _take_last(source: AsyncObservable[TSource]) -> AsyncObservable[TSource]:
        async def subscribe_async(aobv: AsyncObserver[TSource]) -> AsyncDisposable:
            safe_obv, auto_detach = auto_detach_observer(aobv)
            queue: List[TSource] = []

            async def asend(value: TSource) -> None:
                queue.append(value)
                if len(queue) > count:
                    queue.pop(0)

            async def athrow(ex: Exception) -> None:
                await safe_obv.athrow(ex)

            async def aclose() -> None:
                for item in queue:
                    await safe_obv.asend(item)
                await safe_obv.aclose()

            obv = AsyncAnonymousObserver(asend, athrow, aclose)
            return await pipe(obv, source.subscribe_async, auto_detach)

        return AsyncAnonymousObservable(subscribe_async)

    return _take_last


def take_until(other: AsyncObservable[TResult]) -> Stream[TSource, TSource]:
    """Take elements until other.

    Returns the values from the source observable sequence until the
    other observable sequence produces a value.

    Args:
        other: The other async observable

    Returns:
        Stream[TSource, TSource]: [description]
    """

    def _take_until(source: AsyncObservable[TSource]) -> AsyncObservable[TSource]:
        async def subscribe_async(aobv: AsyncObserver[TSource]) -> AsyncDisposable:
            safe_obv, auto_detach = auto_detach_observer(aobv)

            async def asend(value: TSource) -> None:
                await safe_obv.aclose()

            async def athrow(ex: Exception) -> None:
                await safe_obv.athrow(ex)

            obv = AsyncAnonymousObserver(asend, athrow)
            sub2 = await pipe(obv, other.subscribe_async)
            sub1 = await pipe(safe_obv, source.subscribe_async, auto_detach)

            return AsyncDisposable.composite(sub1, sub2)

        return AsyncAnonymousObservable(subscribe_async)

    return _take_until
