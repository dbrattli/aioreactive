import dataclasses
from dataclasses import dataclass
from typing import Any, Callable, Generic, Iterable, NewType, Tuple, TypeVar, cast

from expression.collections import FrozenList, Map, frozenlist, map
from expression.core import MailboxProcessor, pipe
from expression.system import AsyncDisposable

from .create import of_seq
from .msg import CompletedMsg, DisposeMsg_, InnerCompletedMsg, InnerObservableMsg, Msg
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
                    msg = await inbox.receive()
                    new_model = await update(msg, model)
                    return await message_loop(new_model)

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
