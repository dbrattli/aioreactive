import dataclasses
import logging
from dataclasses import dataclass
from typing import Any, Callable, Generic, Iterable, NoReturn, Tuple, TypeVar, cast

from expression.collections import FrozenList, Map, frozenlist, map
from expression.core import (
    MailboxProcessor,
    Nothing,
    Option,
    Some,
    TailCall,
    TailCallResult,
    match,
    pipe,
    tailrec_async,
)
from expression.system import AsyncDisposable

from .create import of_seq
from .msg import CompletedMsg, DisposeMsg, InnerCompletedMsg, InnerObservableMsg, Key, Msg, OtherMsg, SourceMsg
from .notification import Notification, OnError, OnNext
from .observables import AsyncAnonymousObservable
from .observers import AsyncAnonymousObserver, AsyncNotificationObserver, auto_detach_observer
from .types import AsyncObservable, AsyncObserver, Stream

TSource = TypeVar("TSource")
TResult = TypeVar("TResult")
TOther = TypeVar("TOther")


log = logging.getLogger(__name__)


@dataclass
class Model(Generic[TSource]):
    subscriptions: Map[Key, AsyncDisposable]
    queue: FrozenList[AsyncObservable[TSource]]
    is_stopped: bool
    key: Key

    def replace(self, **changes: Any) -> "Model[TSource]":
        """Return a new model."""
        return dataclasses.replace(self, **changes)


def merge_inner(
    max_concurrent: int = 0,
) -> Callable[[AsyncObservable[AsyncObservable[TSource]]], AsyncObservable[TSource]]:
    def _(source: AsyncObservable[AsyncObservable[TSource]]) -> AsyncObservable[TSource]:
        async def subscribe_async(aobv: AsyncObserver[TSource]) -> AsyncDisposable:
            safe_obv, auto_detach = auto_detach_observer(aobv)

            initial_model = Model(
                subscriptions=map.empty,
                queue=frozenlist.empty,
                is_stopped=False,
                key=Key(0),
            )

            async def worker(inbox: MailboxProcessor[Msg[TSource]]) -> None:
                def obv(key: Key) -> AsyncObserver[TSource]:
                    async def asend(value: TSource) -> None:
                        await safe_obv.asend(value)

                    async def athrow(error: Exception) -> None:
                        await safe_obv.athrow(error)

                    async def aclose() -> None:
                        inbox.post(InnerCompletedMsg(key))

                    return AsyncAnonymousObserver(asend, athrow, aclose)

                async def update(msg: Msg[TSource], model: Model[TSource]) -> Model[TSource]:
                    # log.debug("update: %s, model: %s", msg, model)
                    with match(msg) as case:
                        for xs in case(InnerObservableMsg[TSource]):
                            if max_concurrent == 0 or len(model.subscriptions) < max_concurrent:
                                inner = await xs.subscribe_async(obv(model.key))
                                return model.replace(
                                    subscriptions=model.subscriptions.add(model.key, inner),
                                    key=Key(model.key + 1),
                                )
                            lst = FrozenList.singleton(xs)
                            return model.replace(queue=model.queue.append(lst))
                        for key in case(InnerCompletedMsg):
                            subscriptions = model.subscriptions.remove(key)
                            if len(model.queue):
                                xs = model.queue[0]
                                inner = await xs.subscribe_async(obv(model.key))

                                return model.replace(
                                    subscriptions=subscriptions.add(model.key, inner),
                                    key=model.key + 1,
                                    queue=model.queue.tail(),
                                )
                            elif len(subscriptions):
                                return model.replace(subscriptions=subscriptions)
                            else:
                                if model.is_stopped:
                                    await safe_obv.aclose()
                                return model.replace(subscriptions=map.empty)
                        while case(CompletedMsg):
                            if not model.subscriptions:
                                log.debug("merge_inner: closing!")
                                await safe_obv.aclose()

                            return model.replace(is_stopped=True)

                        while case.default():
                            for dispose in model.subscriptions.values():
                                await dispose.dispose_async()

                        return initial_model.replace(is_stopped=True)

                async def message_loop(model: Model[TSource]) -> None:
                    while True:
                        msg = await inbox.receive()
                        model = await update(msg, model)

                        if model.is_stopped and not model.subscriptions:
                            break

                await message_loop(initial_model)

            agent = MailboxProcessor.start(worker)

            async def asend(xs: AsyncObservable[TSource]) -> None:
                log.debug("merge_inner:asend(%s)", xs)
                agent.post(InnerObservableMsg(inner_observable=xs))

            async def athrow(error: Exception) -> None:
                await safe_obv.athrow(error)
                agent.post(DisposeMsg)

            async def aclose() -> None:
                agent.post(CompletedMsg)

            obv = AsyncAnonymousObserver(asend, athrow, aclose)
            dispose = await auto_detach(source.subscribe_async(obv))

            async def cancel() -> None:
                await dispose.dispose_async()
                agent.post(DisposeMsg)

            return AsyncDisposable.create(cancel)

        return AsyncAnonymousObservable(subscribe_async)

    return _


def concat_seq(sources: Iterable[AsyncObservable[TSource]]) -> AsyncObservable[TSource]:
    """Returns an observable sequence that contains the elements of each
    given sequences, in sequential order."""

    return pipe(
        of_seq(sources),
        merge_inner(1),
    )


def combine_latest(other: AsyncObservable[TOther]) -> Stream[TSource, Tuple[TSource, TOther]]:
    """Combine latest values.

    Merges the specified observable sequences into one observable
    sequence by combining elements of the sources into tuples. Returns
    an observable sequence containing the combined results.

    Args:
        other: The other observable to combine with.

    Returns:
        A partially applied stream that takes the source observable and
        returns the combined observable.
    """

    def _combine_latest(source: AsyncObservable[TSource]) -> AsyncObservable[Tuple[TSource, TOther]]:
        async def subscribe_async(aobv: AsyncObserver[Tuple[TSource, TOther]]) -> AsyncDisposable:
            safe_obv, auto_detach = auto_detach_observer(aobv)

            async def worker(inbox: MailboxProcessor[Msg[TSource]]) -> None:
                @tailrec_async
                async def message_loop(
                    source_value: Option[TSource], other_value: Option[TOther]
                ) -> TailCallResult[NoReturn]:
                    cn = await inbox.receive()

                    async def get_value(n: Notification[Any]) -> Option[Any]:
                        with match(n) as m:
                            for value in case(OnNext[TSource]):
                                return Some(value)

                            for err in case(OnError):
                                await safe_obv.athrow(err)

                            while m.default():
                                await safe_obv.aclose()
                        return Nothing

                    with match(cn) as case:
                        for value in case(SourceMsg[TSource]):
                            source_value = await get_value(value)
                            break

                        for value in case(OtherMsg[TOther]):
                            other_value = await get_value(value)
                            break

                    def binder(s: TSource) -> Option[Tuple[TSource, TOther]]:
                        def mapper(o: TOther) -> Tuple[TSource, TOther]:
                            return (s, o)

                        return other_value.map(mapper)

                    combined = source_value.bind(binder)
                    for x in combined.to_list():
                        await safe_obv.asend(x)

                    return TailCall(source_value, other_value)

                await message_loop(Nothing, Nothing)

            agent = MailboxProcessor.start(worker)

            async def obv_fn1(n: Notification[TSource]) -> None:
                pipe(SourceMsg(n), agent.post)

            async def obv_fn2(n: Notification[TOther]) -> None:
                pipe(OtherMsg(n), agent.post)

            obv1: AsyncObserver[TSource] = AsyncNotificationObserver(obv_fn1)
            obv2: AsyncObserver[TOther] = AsyncNotificationObserver(obv_fn2)
            dispose1 = await pipe(obv1, source.subscribe_async, auto_detach)
            dispose2 = await pipe(obv2, other.subscribe_async, auto_detach)

            return AsyncDisposable.composite(dispose1, dispose2)

        return AsyncAnonymousObservable(subscribe_async)

    return _combine_latest


def with_latest_from(other: AsyncObservable[TOther]) -> Stream[TSource, Tuple[TSource, TOther]]:
    """[summary]

    Merges the specified observable sequences into one observable
    sequence by combining the values into tuples only when the first
    observable sequence produces an element. Returns the combined
    observable sequence.

    Args:
        other (AsyncObservable[TOther]): [description]

    Returns:
        Stream[TSource, Tuple[TSource, TOther]]: [description]
    """

    def _with_latest_from(source: AsyncObservable[TSource]) -> AsyncObservable[Tuple[TSource, TOther]]:
        async def subscribe_async(aobv: AsyncObserver[Tuple[TSource, TOther]]) -> AsyncDisposable:
            safe_obv, auto_detach = auto_detach_observer(aobv)

            async def worker(inbox: MailboxProcessor[Msg[TSource]]) -> None:
                @tailrec_async
                async def message_loop(latest: Option[TOther]) -> TailCallResult[NoReturn]:
                    cn = await inbox.receive()

                    async def get_value(n: Notification[Any]) -> Option[Any]:
                        with match(n) as case:
                            for value in case(OnNext[TSource]):
                                return Some(value)

                            for err in case(OnError[TSource]):
                                await safe_obv.athrow(err)

                            while case.default():
                                await safe_obv.aclose()
                        return Nothing

                    source_value = Nothing
                    if isinstance(cn, SourceMsg):
                        cn = cast(SourceMsg[TSource], cn)
                        source_value = await get_value(cn.value)
                    else:
                        cn = cast(OtherMsg[TOther], cn)
                        latest = await get_value(cn.value)

                    def binder(s: TSource) -> Option[Tuple[TSource, TOther]]:
                        def mapper(o: TOther) -> Tuple[TSource, TOther]:
                            return (s, o)

                        return latest.map(mapper)

                    combined = source_value.bind(binder)
                    for x in combined.to_list():
                        await safe_obv.asend(x)

                    return TailCall(latest)

                await message_loop(Nothing)

            agent = MailboxProcessor.start(worker)

            async def obv_fn1(n: Notification[TSource]) -> None:
                pipe(SourceMsg(n), agent.post)

            async def obv_fn2(n: Notification[TOther]) -> None:
                pipe(OtherMsg(n), agent.post)

            obv1: AsyncObserver[TSource] = AsyncNotificationObserver(obv_fn1)
            obv2: AsyncObserver[TOther] = AsyncNotificationObserver(obv_fn2)
            dispose1 = await pipe(obv1, source.subscribe_async, auto_detach)
            dispose2 = await pipe(obv2, other.subscribe_async, auto_detach)
            return AsyncDisposable.composite(dispose1, dispose2)

        return AsyncAnonymousObservable(subscribe_async)

    return _with_latest_from


def zip_seq(
    sequence: Iterable[TOther],
) -> Callable[[AsyncObservable[TSource]], AsyncObservable[Tuple[TSource, TOther]]]:
    def _zip_seq(source: AsyncObservable[TSource]) -> AsyncObservable[Tuple[TSource, TOther]]:
        async def subscribe_async(aobv: AsyncObserver[Tuple[TSource, TOther]]) -> AsyncDisposable:
            safe_obv, auto_detach = auto_detach_observer(aobv)

            enumerator = iter(sequence)

            async def asend(x: TSource) -> None:
                try:
                    try:
                        n = next(enumerator)
                        await safe_obv.asend((x, n))
                    except StopIteration:
                        await safe_obv.aclose()
                except Exception as ex:
                    await safe_obv.athrow(ex)

            async def athrow(ex: Exception) -> None:
                await safe_obv.athrow(ex)

            async def aclose() -> None:
                await safe_obv.aclose()

            return await pipe(
                AsyncAnonymousObserver(asend, athrow, aclose),
                source.subscribe_async,
                auto_detach,
            )

        return AsyncAnonymousObservable(subscribe_async)

    return _zip_seq
