from __future__ import annotations

from collections.abc import Awaitable, Callable, Iterable
from typing import Any, TypeVar

from expression.collections import seq
from expression.core import (
    MailboxProcessor,
    Nothing,
    Option,
    Some,
    TailCall,
    TailCallResult,
    compose,
    pipe,
    tailrec_async,
)
from expression.system import AsyncDisposable

from .combine import merge_inner, zip_seq
from .create import fail
from .msg import (
    Key,
    Msg,
)
from .observables import AsyncAnonymousObservable, AsyncObservable
from .observers import AsyncAnonymousObserver, auto_detach_observer
from .types import AsyncObserver


_TSource = TypeVar("_TSource")
_TResult = TypeVar("_TResult")


def transform(
    anext: Callable[
        [
            Callable[
                [_TResult],
                Awaitable[None],
            ],
            _TSource,
        ],
        Awaitable[None],
    ],
) -> Callable[[AsyncObservable[_TSource]], AsyncObservable[_TResult]]:
    def _(source: AsyncObservable[_TSource]) -> AsyncObservable[_TResult]:
        async def subscribe_async(aobv: AsyncObserver[_TResult]) -> AsyncDisposable:
            async def asend(value: _TSource) -> None:
                return await anext(aobv.asend, value)

            obv: AsyncObserver[_TSource] = AsyncAnonymousObserver(asend, aobv.athrow, aobv.aclose)
            sub = await source.subscribe_async(obv)
            return sub

        return AsyncAnonymousObservable(subscribe_async)

    return _


def map_async(
    amapper: Callable[[_TSource], Awaitable[_TResult]],
) -> Callable[[AsyncObservable[_TSource]], AsyncObservable[_TResult]]:
    """Map async.

    Returns an observable sequence whose elements are the result of
    invoking the async mapper function on each element of the
    source.
    """

    async def handler(next: Callable[[_TResult], Awaitable[None]], x: _TSource) -> None:
        b = await amapper(x)
        await next(b)

    return transform(handler)


def starmap_async(
    amapper: Callable[..., Awaitable[_TResult]],
) -> Callable[[AsyncObservable[Any]], AsyncObservable[_TResult]]:
    """Map async spreading arguments to the async mapper.

    Returns an observable sequence whose elements are the result of
    invoking the async mapper function on each element of the
    source.
    """

    async def handler(next: Callable[[_TResult], Awaitable[None]], args: Iterable[Any]) -> None:
        b = await amapper(*args)
        await next(b)

    return transform(handler)


def map(mapper: Callable[[_TSource], _TResult]) -> Callable[[AsyncObservable[_TSource]], AsyncObservable[_TResult]]:
    """Map each element in the stream.

    Returns an observable sequence whose elements are the result of
    invoking the mapper function on each element of the source.
    """

    def handler(next: Callable[[_TResult], Awaitable[None]], x: _TSource) -> Awaitable[None]:
        return next(mapper(x))

    return transform(handler)


def starmap(mapper: Callable[..., _TResult]) -> Callable[[AsyncObservable[Any]], AsyncObservable[_TResult]]:
    """Map and spread the arguments to the mapper.

    Returns an observable sequence whose elements are the result of
    invoking the mapper function on each element of the source.
    """

    def handler(next: Callable[[_TResult], Awaitable[None]], args: Iterable[Any]) -> Awaitable[None]:
        return next(mapper(*args))

    return transform(handler)


def mapi_async(
    mapper: Callable[[_TSource, int], Awaitable[_TResult]],
) -> Callable[[AsyncObservable[_TSource]], AsyncObservable[_TResult]]:
    """Map with index async.

    Returns an observable sequence whose elements are the result of
    invoking the async mapper function by incorporating the element's
    index on each element of the source.
    """
    return compose(
        zip_seq(seq.infinite),
        starmap_async(mapper),
    )


def mapi(
    mapper: Callable[[_TSource, int], _TResult],
) -> Callable[[AsyncObservable[_TSource]], AsyncObservable[_TResult]]:
    """Map with index.

    Returns an observable sequence whose elements are the result of
    invoking the mapper function and incorporating the element's index
    on each element of the source.
    """
    return compose(
        zip_seq(seq.infinite),
        starmap(mapper),
    )


def flat_map(
    mapper: Callable[[_TSource], AsyncObservable[_TResult]],
) -> Callable[[AsyncObservable[_TSource]], AsyncObservable[_TResult]]:
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


def flat_mapi(
    mapper: Callable[[_TSource, int], AsyncObservable[_TResult]],
) -> Callable[[AsyncObservable[_TSource]], AsyncObservable[_TResult]]:
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


def flat_map_async(
    mapper: Callable[[_TSource], Awaitable[AsyncObservable[_TResult]]],
) -> Callable[[AsyncObservable[_TSource]], AsyncObservable[_TResult]]:
    """Flap map async.

    Asynchronously projects each element of an observable sequence into
    an observable sequence and merges the resulting observable sequences
    back into one observable sequence.


    Args:
        mapper: Function to transform each item in the stream.

    Returns:
        Stream[TSource, TResult]: [description]
    """
    return compose(
        map_async(mapper),
        merge_inner(0),
    )


def flat_mapi_async(
    mapper: Callable[[_TSource, int], Awaitable[AsyncObservable[_TResult]]],
) -> Callable[[AsyncObservable[_TSource]], AsyncObservable[_TResult]]:
    """Flat map async with index.

    Asynchronously projects each element of an observable sequence into
    an observable sequence by incorporating the element's index on each
    element of the source. Merges the resulting observable sequences
    back into one observable sequence.

    Args:
        mapper: Function to transform each item in the stream.

    Returns:
        Stream[TSource, TResult]: [description]
    """
    return compose(
        mapi_async(mapper),
        merge_inner(0),
    )


def concat_map(
    mapper: Callable[[_TSource], AsyncObservable[_TResult]],
) -> Callable[[AsyncObservable[_TSource]], AsyncObservable[_TResult]]:
    return compose(
        map(mapper),
        merge_inner(1),
    )


def switch_latest(
    source: AsyncObservable[AsyncObservable[_TSource]],
) -> AsyncObservable[_TSource]:
    """Switch latest observable.

    Transforms an observable sequence of observable sequences into an
    observable sequence producing values only from the most recent
    observable sequence

    Args:
        source: The source observable of obsevables sequence.

    Returns:
        The transformed observable sequence.
    """

    async def subscribe_async(aobv: AsyncObserver[_TSource]) -> AsyncDisposable:
        safe_obv, auto_detach = auto_detach_observer(aobv)

        def obv(mb: MailboxProcessor[Msg[_TSource]], id: int) -> AsyncObserver[_TSource]:
            async def asend(value: _TSource) -> None:
                await safe_obv.asend(value)

            async def athrow(error: Exception) -> None:
                await safe_obv.athrow(error)

            async def aclose() -> None:
                pipe(
                    Msg[Any](inner_completed=Key(id)),
                    mb.post,
                )

            return AsyncAnonymousObserver(asend, athrow, aclose)

        async def worker(inbox: MailboxProcessor[Msg[_TSource]]) -> None:
            @tailrec_async
            async def message_loop(
                current: Option[AsyncDisposable], is_stopped: bool, current_id: int
            ) -> TailCallResult[None, [Option[AsyncDisposable], bool, int]]:
                cmd = await inbox.receive()

                match cmd:
                    case Msg(tag="inner_observable", inner_observable=xs):
                        next_id = current_id + 1
                        for disp in current.to_list():
                            await disp.dispose_async()
                        inner = await xs.subscribe_async(obv(inbox, next_id))
                        current, current_id = Some(inner), next_id

                    case Msg(tag="inner_completed", inner_completed=idx):
                        if is_stopped and idx == current_id:
                            await safe_obv.aclose()
                            current, is_stopped = Nothing, True

                    case Msg(tag="completed"):
                        if current.is_none():
                            await safe_obv.aclose()

                    case Msg(tag="dispose"):
                        if current.is_some():
                            await current.value.dispose_async()
                        current, is_stopped = Nothing, True
                    case _:
                        raise ValueError(f"Unknown message: {cmd}")

                return TailCall[Option[AsyncDisposable], bool, int](current, is_stopped, current_id)

            await message_loop(Nothing, False, 0)

        inner_agent = MailboxProcessor.start(worker)

        async def asend(xs: AsyncObservable[_TSource]) -> None:
            pipe(
                Msg(inner_observable=xs),
                inner_agent.post,
            )

        async def athrow(error: Exception) -> None:
            await safe_obv.athrow(error)

        async def aclose() -> None:
            inner_agent.post(Msg(completed=True))

        _obv = AsyncAnonymousObserver(asend, athrow, aclose)
        dispose = await pipe(
            _obv,
            source.subscribe_async,
            auto_detach,
        )

        async def cancel() -> None:
            await dispose.dispose_async()
            inner_agent.post(Msg(dispose=True))

        return AsyncDisposable.create(cancel)

    return AsyncAnonymousObservable(subscribe_async)


def flat_map_latest_async(
    mapper: Callable[[_TSource], Awaitable[AsyncObservable[_TResult]]],
) -> Callable[[AsyncObservable[_TSource]], AsyncObservable[_TResult]]:
    """Flat map latest async.

    Asynchronosly transforms the items emitted by an source sequence
    into observable streams, and mirror those items emitted by the
    most-recently transformed observable sequence.

    Args:
        mapper (Callable[[TSource]): [description]
        Awaitable ([type]): [description]

    Returns:
        Stream[TSource, TResult]: [description]
    """
    return compose(map_async(mapper), switch_latest)


def flat_map_latest(
    mapper: Callable[[_TSource], AsyncObservable[_TResult]],
) -> Callable[[AsyncObservable[_TSource]], AsyncObservable[_TResult]]:
    """Flat map latest.

    Transforms the items emitted by an source sequence into observable
    streams, and mirror those items emitted by the most-recently
    transformed observable sequence.

    Args:
        mapper (Callable[[TSource, AsyncObservable[TResult]]): [description]

    Returns:
        Stream[TSource, TResult]: [description]
    """
    return compose(map(mapper), switch_latest)


def catch(
    handler: Callable[[Exception], AsyncObservable[_TSource]],
) -> Callable[[AsyncObservable[_TSource]], AsyncObservable[_TSource]]:
    """Catch Exception.

    Returns an observable sequence containing the first sequence's
    elements, followed by the elements of the handler sequence in case
    an exception occurred.

    Args:
        handler: Exception handler.

    Returns:
        A new stream that replaces the original one.
    """

    def _catch(source: AsyncObservable[_TSource]) -> AsyncObservable[_TSource]:
        async def subscribe_async(aobv: AsyncObserver[_TSource]) -> AsyncDisposable:
            disposable = AsyncDisposable.empty()

            async def action(source: AsyncObservable[_TSource]) -> None:
                nonlocal disposable

                async def asend(value: _TSource) -> None:
                    await aobv.asend(value)

                async def athrow(error: Exception) -> None:
                    next_source = handler(error)
                    await action(next_source)

                async def aclose() -> None:
                    await aobv.aclose()

                _obv = AsyncAnonymousObserver(asend, athrow, aclose)

                await disposable.dispose_async()
                subscription = await source.subscribe_async(_obv)
                disposable = subscription

            await action(source)

            return AsyncDisposable.create(disposable.dispose_async)

        return AsyncAnonymousObservable(subscribe_async)

    return _catch


def retry(
    retry_count: int,
) -> Callable[[AsyncObservable[_TSource]], AsyncObservable[_TSource]]:
    def _retry(source: AsyncObservable[_TSource]) -> AsyncObservable[_TSource]:
        count = retry_count

        def factory(exn: Exception) -> AsyncObservable[_TSource]:
            nonlocal count

            if not count:
                return fail(exn)
            else:
                count -= count
                return source

        return pipe(source, catch(factory))

    return _retry


def _scan(
    accumulator: Callable[[_TResult, _TSource], Awaitable[_TResult]],
    initial: _TResult,
) -> Callable[[AsyncObservable[_TSource]], AsyncObservable[_TResult]]:
    def _scan_operator(obs: AsyncObservable[_TSource]) -> AsyncObservable[_TResult]:
        async def subscribe_async(observer: AsyncObserver[_TResult]) -> AsyncDisposable:
            disposable: AsyncDisposable = AsyncDisposable.empty()
            current: _TResult = initial

            async def anext(value: _TSource) -> None:
                nonlocal current

                try:
                    intermediate = await accumulator(current, value)
                except Exception as ex:
                    await observer.athrow(ex)
                else:
                    current = intermediate

                    await observer.asend(current)

            async def athrow(exception: Exception) -> None:
                await observer.athrow(exception)

            async def aclose() -> None:
                await observer.aclose()

            await disposable.dispose_async()
            disposable = await obs.subscribe_async(anext, athrow, aclose)

            return disposable

        return AsyncAnonymousObservable(subscribe_async)

    return _scan_operator


def scan(
    accumulator: Callable[[_TResult, _TSource], _TResult],
    initial: _TResult,
) -> Callable[[AsyncObservable[_TSource]], AsyncObservable[_TResult]]:
    async def async_accumulator(state: _TResult, current: _TSource) -> _TResult:
        return accumulator(state, current)

    return _scan(async_accumulator, initial)


def scan_async(
    accumulator: Callable[[_TResult, _TSource], Awaitable[_TResult]],
    initial: _TResult,
) -> Callable[[AsyncObservable[_TSource]], AsyncObservable[_TResult]]:
    """Async version of the scan operator.

    Args:
        accumulator: An async accumulator function.
        initial: The initial state.

    Returns:
        The scan operator.
    """
    return _scan(accumulator, initial)


def reduce(
    accumulator: Callable[[_TResult, _TSource], _TResult],
    initial: _TResult,
) -> Callable[[AsyncObservable[_TSource]], AsyncObservable[_TResult]]:
    async def _reduce(current: _TResult, value: _TSource) -> _TResult:
        return accumulator(current, value)

    def _operator(Observable: AsyncObservable[_TSource]) -> AsyncObservable[_TResult]:
        return pipe(Observable, reduce_async(_reduce, initial))

    return _operator


def reduce_async(
    accumulator: Callable[[_TResult, _TSource], Awaitable[_TResult]],
    initial: _TResult,
) -> Callable[[AsyncObservable[_TSource]], AsyncObservable[_TResult]]:
    def _operator(source: AsyncObservable[_TSource]) -> AsyncObservable[_TResult]:
        from .filtering import take_last

        return pipe(source, scan_async(accumulator, initial), take_last(1))

    return _operator
