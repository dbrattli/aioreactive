import dataclasses
from dataclasses import dataclass
from typing import Any, Callable, Generic, Iterable, NewType, Tuple, TypeVar, cast

from expression.collections import FrozenList, Map, frozenlist, map
from expression.core import MailboxProcessor
from expression.system import AsyncDisposable

from .observables import AsyncAnonymousObservable
from .observers import AsyncAnonymousObserver, auto_detach_observer
from .types import AsyncObservable, AsyncObserver

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


class Msg:
    pass


@dataclass
class InnerObservable(Msg, Generic[TSource]):
    inner_observable: AsyncObservable[TSource]


@dataclass
class InnerCompleted(Msg):
    key: Key


@dataclass
class OuterCompleted(Msg):
    pass


@dataclass
class Dispose(Msg):
    pass


def merge_inner(max_concurrent: int) -> Callable[[AsyncObservable[TSource]], AsyncObservable[TSource]]:
    def _(source: AsyncObservable[AsyncObservable[TSource]]) -> AsyncObservable[TSource]:
        async def subscribe_async(aobv: AsyncObserver[TSource]) -> AsyncDisposable:
            safe_obv, auto_detach = auto_detach_observer(aobv)

            initial_model = Model(subscriptions=map.empty, queue=frozenlist.empty, is_stopped=False, key=Key(0))

            async def worker(inbox: MailboxProcessor[Msg]) -> None:
                def obv(key: Key) -> AsyncObserver[TSource]:
                    async def asend(value: TSource) -> None:
                        await safe_obv.asend(value)

                    async def athrow(error: Exception) -> None:
                        await safe_obv.athrow(error)

                    async def aclose() -> None:
                        inbox.post(InnerCompleted(key))

                    return AsyncAnonymousObserver(asend, athrow, aclose)

                async def update(msg: Msg, model: Model[TSource]) -> Model[TSource]:
                    if isinstance(msg, InnerObservable):
                        msg = cast(InnerObservable[TSource], msg)
                        xs: AsyncObservable[TSource] = msg.inner_observable
                        if max_concurrent == 0 and len(model.subscriptions) < max_concurrent:
                            inner = await xs.subscribe_async(obv(model.key))
                            return model.replace(
                                subscriptions=model.subscriptions.add(model.key, inner),
                                key=Key(model.key + 1),
                            )
                        else:
                            return model.replace(queue=model.queue.append(frozenlist.singleton(xs)))
                    elif isinstance(msg, InnerCompleted):
                        key = msg.key
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
                    elif isinstance(msg, OuterCompleted):
                        if len(model.subscriptions):
                            await safe_obv.aclose()
                        return model.replace(is_stopped=True)
                    else:
                        for key, dispose in model.subscriptions:
                            await dispose.dispose_async()
                        return initial_model

                async def message_loop(model: Model[TSource]) -> None:
                    msg = await inbox.receive()
                    new_model = await update(msg, model)
                    return await message_loop(new_model)

                await message_loop(initial_model)

            agent = MailboxProcessor.start(worker)

            async def asend(xs: TSource) -> None:
                agent.post(InnerObservable(inner_observable=xs))

            async def athrow(error: Exception) -> None:
                await safe_obv.athrow(error)
                agent.post(Dispose())

            async def aclose() -> None:
                agent.post(OuterCompleted())

            obv = AsyncAnonymousObserver(asend, athrow, aclose)
            dispose = await auto_detach(source.subscribe_async(obv))

            async def cancel() -> None:
                await dispose.dispose_async()
                agent.post(Dispose())

            return AsyncDisposable.create(cancel)

        return AsyncAnonymousObservable(subscribe_async)

    return _


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

            _obv = AsyncAnonymousObserver(asend, athrow, aclose)
            return await auto_detach(source.subscribe_async(_obv))

        return AsyncAnonymousObservable(subscribe_async)

    return _
