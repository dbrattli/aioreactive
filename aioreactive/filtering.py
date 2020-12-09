from typing import Any, Awaitable, Callable, List, NoReturn, Optional, Tuple, TypeVar, overload

from expression.collections import seq
from expression.core import (
    MailboxProcessor,
    Option,
    TailCall,
    TailCallResult,
    aiotools,
    compose,
    fst,
    match,
    pipe,
    tailrec_async,
)
from expression.system.disposable import AsyncDisposable

from .combine import zip_seq
from .notification import Notification, OnCompleted, OnError, OnNext
from .observables import AsyncAnonymousObservable
from .observers import AsyncAnonymousObserver, AsyncNotificationObserver, auto_detach_observer
from .transform import map, transform
from .types import AsyncObservable, AsyncObserver, Stream

TSource = TypeVar("TSource")
TResult = TypeVar("TResult")


def choose_async(chooser: Callable[[TSource], Awaitable[Option[TResult]]]) -> Stream[TSource, TResult]:
    async def handler(next: Callable[[TResult], Awaitable[None]], xs: TSource) -> None:
        result = await chooser(xs)
        for x in result.to_list():
            await next(x)

    return transform(handler)


def choose(chooser: Callable[[TSource], Option[TResult]]) -> Stream[TSource, TResult]:
    def handler(next: Callable[[TResult], Awaitable[None]], xs: TSource) -> Awaitable[None]:
        for x in chooser(xs).to_list():
            return next(x)
        return aiotools.empty()

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
        if await predicate(x):
            return await next(x)

    return transform(handler)


def filter(predicate: Callable[[TSource], bool]) -> Stream[TSource, TSource]:
    def handler(next: Callable[[TSource], Awaitable[None]], x: TSource) -> Awaitable[None]:
        if predicate(x):
            return next(x)
        return aiotools.empty()

    return transform(handler)


@overload
def starfilter(predicate: Callable[[TSource, int], bool]) -> Stream[Tuple[TSource, int], Tuple[TSource, int]]:
    ...


def starfilter(predicate: Callable[..., bool]) -> Stream[Tuple[Any, ...], Tuple[Any, ...]]:
    """Filter and spread the arguments to the predicate.

    Filters the elements of an observable sequence based on a predicate.
    Returns:
        An observable sequence that contains elements from the input
        sequence that satisfy the condition.
    """

    def handler(next: Callable[[Tuple[TSource, ...]], Awaitable[None]], args: Tuple[TSource, ...]) -> Awaitable[None]:
        if predicate(*args):
            return next(args)
        return aiotools.empty()

    return transform(handler)


def filteri(predicate: Callable[[TSource, int], bool]) -> Stream[TSource, TSource]:
    return compose(
        zip_seq(seq.infinite),
        starfilter(predicate),
        map(fst),
    )


def distinct_until_changed(source: AsyncObservable[TSource]) -> AsyncObservable[TSource]:
    """Distinct until changed.

    Return an observable sequence only containing the distinct
    contiguous elements from the source sequence.

    Args:
        source (AsyncObservable[TSource]): [description]

    Returns:
        Async observable with only contiguous distinct elements.
    """

    async def subscribe_async(aobv: AsyncObserver[TSource]) -> AsyncDisposable:
        safe_obv, auto_detach = auto_detach_observer(aobv)

        async def worker(inbox: MailboxProcessor[Notification[TSource]]) -> None:
            @tailrec_async
            async def message_loop(latest: Notification[TSource]) -> TailCallResult[NoReturn]:
                n = await inbox.receive()

                async def get_latest() -> Notification[TSource]:
                    with match(n) as case:
                        for x in case(OnNext[TSource]):
                            if n == latest:
                                break
                            try:
                                await safe_obv.asend(x)
                            except Exception as ex:
                                await safe_obv.athrow(ex)
                            break
                        for err in case(OnError[TSource]):
                            await safe_obv.athrow(err)
                            break
                        while case(OnCompleted):
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

            obv = AsyncAnonymousObserver(asend, safe_obv.athrow, safe_obv.aclose)
            return await pipe(obv, source.subscribe_async, auto_detach)

        return AsyncAnonymousObservable(subscribe_async)

    return _skip


def skip_last(count: int) -> Stream[TSource, TSource]:
    def _skip_last(source: AsyncObservable[TSource]) -> AsyncObservable[TSource]:
        async def subscribe_async(observer: AsyncObserver[TSource]) -> AsyncDisposable:
            safe_obv, auto_detach = auto_detach_observer(observer)

            q = []

            async def asend(value: TSource) -> None:
                front = None
                q.append(value)
                if len(q) > count:
                    front = q.pop(0)

                if front is not None:
                    await safe_obv.asend(front)

            obv = AsyncAnonymousObserver(asend, safe_obv.athrow, safe_obv.aclose)
            return await pipe(obv, source.subscribe_async, auto_detach)

        return AsyncAnonymousObservable(subscribe_async)

    return _skip_last


def take(count: int) -> Stream[TSource, TSource]:
    if count < 0:
        raise ValueError("Count cannot be negative.")

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

            obv = AsyncAnonymousObserver(asend, safe_obv.athrow, safe_obv.aclose)
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

            async def aclose() -> None:
                for item in queue:
                    await safe_obv.asend(item)
                await safe_obv.aclose()

            obv = AsyncAnonymousObserver(asend, safe_obv.athrow, aclose)
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

            obv = AsyncAnonymousObserver(asend, safe_obv.athrow)
            sub2 = await pipe(obv, other.subscribe_async)
            sub1 = await pipe(safe_obv, source.subscribe_async, auto_detach)

            return AsyncDisposable.composite(sub1, sub2)

        return AsyncAnonymousObservable(subscribe_async)

    return _take_until


def slice(start: Optional[int] = None, stop: Optional[int] = None, step: int = 1) -> Stream[TSource, TSource]:
    """Slices the given source stream.

    It is basically a wrapper around skip(), skip_last(), take(),
    take_last() and filter().
    This marble diagram helps you remember how slices works with
    streams. Positive numbers is relative to the start of the events,
    while negative numbers are relative to the end (on_completed) of the
    stream.

    ```
     r---e---a---c---t---i---v---e---|
     0   1   2   3   4   5   6   7   8
    -8  -7  -6  -5  -4  -3  -2  -1
    ```

    Example:
    >>> result = slice(1, 10, source)
    >>> result = slice(1, -2, source)
    >>> result = slice(1, -1, 2, source)

    Args:
        start: Number of elements to skip of take last
        stop: Last element to take of skip last
        step: Takes every step element. Must be larger than zero

    Returns:
        A sliced source stream.
    """

    def _slice(source: AsyncObservable[TSource]) -> AsyncObservable[TSource]:
        nonlocal start

        if start is not None:
            if start < 0:
                source = pipe(source, take_last(abs(start)))
            else:
                source = pipe(source, skip(start))

        if stop is not None:
            if stop > 0:
                start = start or 0
                source = pipe(source, take(stop - start))
            else:
                source = pipe(source, skip_last(abs(stop)))

        if step is not None:
            if step > 1:
                mapper: Callable[[Any, int], bool] = lambda _, i: i % step == 0
                source = pipe(source, filteri(mapper))
            elif step < 0:
                # Reversing streams is not supported
                raise TypeError("Negative step not supported.")

        return source

    return _slice
