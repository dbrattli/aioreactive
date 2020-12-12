from typing import Any, Awaitable, Callable, Tuple, TypeVar, overload

from expression.collections import seq
from expression.core import (
    MailboxProcessor,
    Nothing,
    Option,
    Some,
    TailCall,
    TailCallResult,
    compose,
    match,
    pipe,
    tailrec_async,
)
from expression.system import AsyncDisposable

from .combine import merge_inner, zip_seq
from .create import fail
from .msg import CompletedMsg, DisposeMsg, InnerCompletedMsg, InnerObservableMsg, Key, Msg
from .observables import AsyncAnonymousObservable, AsyncObservable
from .observers import AsyncAnonymousObserver, auto_detach_observer
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
            async def asend(value: TResult) -> None:
                return await anext(aobv.asend, value)

            obv: AsyncObserver[TSource] = AsyncAnonymousObserver(asend, aobv.athrow, aobv.aclose)
            sub = await source.subscribe_async(obv)
            return sub

        return AsyncAnonymousObservable(subscribe_async)

    return _


def map_async(amapper: Callable[[TSource], Awaitable[TResult]]) -> Stream[TSource, TResult]:
    """Returns an observable sequence whose elements are the result of
    invoking the async mapper function on each element of the
    source."""

    async def handler(next: Callable[[TResult], Awaitable[None]], x: TSource) -> None:
        b = await amapper(x)
        await next(b)

    return transform(handler)


@overload
def starmap_async(mapper: Callable[[TSource, int], Awaitable[TResult]]) -> Stream[TSource, TResult]:
    ...


def starmap_async(amapper: Callable[..., Awaitable[TResult]]) -> Stream[Tuple[TSource, ...], TResult]:
    """Map async spreading arguments to the async mapper.

    Returns an observable sequence whose elements are the result of
    invoking the async mapper function on each element of the
    source."""

    async def handler(next: Callable[[TResult], Awaitable[None]], args: Tuple[TSource, ...]) -> None:
        b = await amapper(*args)
        await next(b)

    return transform(handler)


def map(mapper: Callable[[TSource], TResult]) -> Stream[TSource, TResult]:
    """Map each element in the stream.

    Returns an observable sequence whose elements are the result of
    invoking the mapper function on each element of the source."""

    def handler(next: Callable[[TResult], Awaitable[None]], x: TSource) -> Awaitable[None]:
        return next(mapper(x))

    return transform(handler)


@overload
def starmap(mapper: Callable[[TSource, int], TResult]) -> Stream[Tuple[TSource, int], TResult]:
    ...


def starmap(mapper: Callable[..., TResult]) -> Stream[Tuple[TSource, ...], TResult]:
    """Map and spread the arguments to the mapper.

    Returns an observable sequence whose elements are the result of
    invoking the mapper function on each element of the source."""

    def handler(next: Callable[[TResult], Awaitable[None]], args: Tuple[Any, ...]) -> Awaitable[None]:
        return next(mapper(*args))

    return transform(handler)


def mapi_async(mapper: Callable[[TSource, int], Awaitable[TResult]]) -> Stream[TSource, TResult]:
    """Map with index async.

    Returns an observable sequence whose elements are the result of
    invoking the async mapper function by incorporating the element's
    index on each element of the source.
    """
    return compose(zip_seq(seq.infinite), starmap_async(mapper))


def mapi(mapper: Callable[[TSource, int], TResult]) -> Stream[TSource, TResult]:
    """Map with index.

    Returns an observable sequence whose elements are the result of
    invoking the mapper function and incorporating the element's index
    on each element of the source.
    """
    return compose(
        zip_seq(seq.infinite),
        starmap(mapper),
    )


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


def switch_latest(source: AsyncObservable[AsyncObservable[TSource]]) -> AsyncObservable[TSource]:
    """Switch latest observable.

    Transforms an observable sequence of observable sequences into an
    observable sequence producing values only from the most recent
    observable sequence

    Args:
        source: The source observable of obsevables sequence.

    Returns:
        The transformed observable sequence.
    """

    async def subscribe_async(aobv: AsyncObserver[TSource]) -> AsyncDisposable:
        safe_obv, auto_detach = auto_detach_observer(aobv)

        def obv(mb: MailboxProcessor[Msg[TSource]], id: int):
            async def asend(value: TSource) -> None:
                await safe_obv.asend(value)

            async def athrow(error: Exception) -> None:
                await safe_obv.athrow(error)

            async def aclose() -> None:
                pipe(Key(id), InnerCompletedMsg, mb.post)

            return AsyncAnonymousObserver(asend, athrow, aclose)

        async def worker(inbox: MailboxProcessor[Msg[TSource]]) -> None:
            @tailrec_async
            async def message_loop(
                current: Option[AsyncDisposable], is_stopped: bool, current_id: int
            ) -> TailCallResult[None]:
                cmd = await inbox.receive()

                with match(cmd) as case:
                    for xs in case(InnerObservableMsg[TSource]):
                        next_id = current_id + 1
                        for disp in current.to_list():
                            await disp.dispose_async()
                        inner = await xs.subscribe_async(obv(inbox, next_id))
                        current, current_id = Some(inner), next_id
                        break
                    for idx in case(InnerCompletedMsg):
                        if is_stopped and idx == current_id:
                            await safe_obv.aclose()
                            current, is_stopped = Nothing, True
                        break
                    while case(CompletedMsg):
                        if current.is_none():
                            await safe_obv.aclose()
                        break
                    while case(DisposeMsg):
                        if current.is_some():
                            await current.value.dispose_async()
                        current, is_stopped = Nothing, True
                        break

                return TailCall(current, is_stopped, current_id)

            await message_loop(Nothing, False, 0)

        inner_agent = MailboxProcessor.start(worker)

        async def asend(xs: AsyncObservable[TSource]) -> None:
            pipe(
                xs,
                InnerObservableMsg,
                inner_agent.post,
            )

        async def athrow(error: Exception) -> None:
            await safe_obv.athrow(error)

        async def aclose() -> None:
            inner_agent.post(CompletedMsg)

        _obv = AsyncAnonymousObserver(asend, athrow, aclose)
        dispose = await pipe(
            _obv,
            AsyncObserver,
            source.subscribe_async,
            auto_detach,
        )

        async def cancel() -> None:
            await dispose.dispose_async()
            inner_agent.post(DisposeMsg)

        return AsyncDisposable.create(cancel)

    return AsyncAnonymousObservable(subscribe_async)


def flat_map_latest_async(mapper: Callable[[TSource], Awaitable[AsyncObservable[TResult]]]) -> Stream[TSource, TResult]:
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


def flat_map_latest(mapper: Callable[[TSource], AsyncObservable[TResult]]) -> Stream[TSource, TResult]:
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


def catch(handler: Callable[[Exception], AsyncObservable[TSource]]) -> Stream[TSource, TSource]:
    """Catch Exception.

    Returns an observable sequence containing the first sequence's
    elements, followed by the elements of the handler sequence in case
    an exception occurred.

    Args:
        handler: Exception handler.

    Returns:
        A new stream that replaces the original one.
    """

    def _catch(source: AsyncObservable[TSource]) -> AsyncObservable[TSource]:
        async def subscribe_async(aobv: AsyncObserver[TSource]) -> AsyncDisposable:
            disposable = AsyncDisposable.empty()

            async def action(source: AsyncObservable[TSource]) -> None:
                nonlocal disposable

                async def asend(value: TSource) -> None:
                    await aobv.asend(value)

                async def athrow(error: Exception) -> None:
                    next_source = handler(error)
                    action(next_source)

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


def retry(retry_count: int) -> Stream[TSource, TSource]:
    def _retry(source: AsyncObservable[TSource]) -> AsyncObservable[TSource]:
        count = retry_count

        def factory(exn: Exception) -> AsyncObservable[TSource]:
            nonlocal count

            if not count:
                return fail(exn)
            else:
                count -= count
                return source

        return pipe(source, catch(factory))

    return _retry
