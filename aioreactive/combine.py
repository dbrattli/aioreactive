import dataclasses
from dataclasses import dataclass
from typing import Any, Callable, Generic, Iterable, NewType, Tuple, TypeVar, cast

from expression.collections import FrozenList, Map, frozenlist, map
from expression.core import MailboxProcessor, Nothing, Option, Result, Some, TailCall, pipe, recursive_async
from expression.system import AsyncDisposable

from .create import of_seq
from .msg import CompletedMsg, DisposeMsg_, InnerCompletedMsg, InnerObservableMsg, Msg, OtherMsg, SourceMsg
from .notification import Notification, OnError, OnNext
from .observables import AsyncAnonymousObservable
from .observers import AsyncAnonymousObserver, AsyncNotificationObserver, auto_detach_observer
from .types import AsyncObservable, AsyncObserver, Stream

TSource = TypeVar("TSource")
TResult = TypeVar("TResult")
TOther = TypeVar("TOther")


Key = NewType("Key", int)


@dataclass
class Model(Generic[TSource]):
    subscriptions: Map[Key, AsyncDisposable]
    queue: FrozenList[AsyncObservable[TSource]]
    is_stopped: bool
    key: Key

    def replace(self, **changes: Any) -> "Model[TSource]":
        """Return a new model."""
        return dataclasses.replace(self, **changes)


def merge_inner(max_concurrent: int) -> Callable[[AsyncObservable[TSource]], AsyncObservable[TSource]]:
    def _(source: AsyncObservable[AsyncObservable[TSource]]) -> AsyncObservable[TSource]:
        async def subscribe_async(aobv: AsyncObserver[TSource]) -> AsyncDisposable:
            safe_obv, auto_detach = auto_detach_observer(aobv)

            initial_model = Model(
                subscriptions=map.empty,
                queue=frozenlist.empty,
                is_stopped=False,
                key=Key(0),
            )

            async def worker(inbox: MailboxProcessor[Msg]) -> None:
                def obv(key: Key) -> AsyncObserver[TSource]:
                    async def asend(value: TSource) -> None:
                        await safe_obv.asend(value)

                    async def athrow(error: Exception) -> None:
                        await safe_obv.athrow(error)

                    async def aclose() -> None:
                        inbox.post(InnerCompletedMsg(key))

                    return AsyncAnonymousObserver(asend, athrow, aclose)

                async def update(msg: Msg, model: Model[TSource]) -> Model[TSource]:
                    if isinstance(msg, InnerObservableMsg):
                        msg = cast(InnerObservableMsg[TSource], msg)
                        xs: AsyncObservable[TSource] = msg.inner_observable
                        if max_concurrent == 0 and len(model.subscriptions) < max_concurrent:
                            inner = await xs.subscribe_async(obv(model.key))
                            return model.replace(
                                subscriptions=model.subscriptions.add(model.key, inner),
                                key=Key(model.key + 1),
                            )
                        else:
                            return model.replace(queue=model.queue.append(frozenlist.singleton(xs)))
                    elif isinstance(msg, InnerCompletedMsg):
                        key = Key(msg.key)
                        subscriptions = model.subscriptions.remove(key)

                        if len(model.queue):
                            xs = model.queue[0]
                            inner = await xs.subscribe_async(obv(model.key))

                            return model.replace(
                                subscriptions=subscriptions.add(model.key, inner),
                                key=model.key + 1,
                                queue=model.queue.tail,
                            )
                        elif len(subscriptions):
                            return model.replace(subscriptions=subscriptions)
                        else:
                            if model.is_stopped:
                                await safe_obv.aclose()
                            return model.replace(subscriptions=map.empty)
                    elif msg is CompletedMsg:
                        if len(model.subscriptions):
                            await safe_obv.aclose()
                        return model.replace(is_stopped=True)
                    else:
                        for key, dispose in model.subscriptions:
                            await dispose.dispose_async()
                        return initial_model

                async def message_loop(model: Model[TSource]) -> None:
                    while True:
                        msg = await inbox.receive()
                        model = await update(msg, model)

                await message_loop(initial_model)

            agent = MailboxProcessor.start(worker)

            async def asend(xs: TSource) -> None:
                agent.post(InnerObservableMsg(inner_observable=xs))

            async def athrow(error: Exception) -> None:
                await safe_obv.athrow(error)
                agent.post(DisposeMsg_)

            async def aclose() -> None:
                agent.post(CompletedMsg)

            obv = AsyncAnonymousObserver(asend, athrow, aclose)
            dispose = await auto_detach(source.subscribe_async(obv))

            async def cancel() -> None:
                await dispose.dispose_async()
                agent.post(DisposeMsg_)

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

    """Merges the specified observable sequences into one observable sequence by combining elements of the sources into
    tuples. Returns an observable sequence containing the combined results."""


def combine_latest(other: AsyncObservable[TOther]) -> Stream[TSource, Tuple[TSource, TOther]]:
    def _combine_latest(source: AsyncObservable[TSource]) -> AsyncObservable[Tuple[TSource, TOther]]:
        async def subscribe_async(aobv: AsyncObserver[Tuple[TSource, TOther]]) -> AsyncDisposable:
            safe_bv, auto_detach = auto_detach_observer(aobv)

            async def worker(inbox: MailboxProcessor[Msg]) -> None:
                @recursive_async
                async def message_loop(
                    source: Option[TSource], other: Option[TOther]
                ) -> Result[AsyncObservable[TSource], Exception]:
                    cn = await inbox.receive()

                    async def on_next_option(n: Notification[TSource]) -> Option[TSource]:
                        if isinstance(n, OnNext):
                            n = cast(OnNext[TSource], n)
                            x = n.value
                            return Some(x)
                        elif isinstance(n, OnError):
                            n = cast(OnError[TSource], n)
                            ex = n.exception
                            await safe_bv.athrow(ex)
                            return Nothing
                        else:
                            await safe_bv.aclose()
                            return Nothing

                    if isinstance(cn, SourceMsg):
                        cn = cast(SourceMsg[TSource], cn)
                        source = await on_next_option(cn.value)
                    else:
                        cn = cast(OtherMsg[TOther], cn)
                        other = await on_next_option(cn.value)

                    def binder(s: TSource) -> Option[Tuple[TSource, TResult]]:
                        def mapper(o: TOther) -> Tuple[TSource, TResult]:
                            return (s, o)

                        return other.map(mapper)

                    combined = source.bind(binder)
                    for x in combined.to_list():
                        await safe_bv.asend(x)

                    return TailCall(source, other)

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


def zip_seq(
    sequence: Iterable[TOther],
) -> Callable[[AsyncObservable[TSource]], AsyncObservable[Tuple[TSource, TOther]]]:
    def _(source: AsyncObservable[TSource]) -> AsyncObservable[Tuple[TSource, TOther]]:
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

    return _
