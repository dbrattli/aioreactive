import asyncio
import logging
import time
from datetime import datetime, timedelta
from typing import Iterable, Tuple, TypeVar

from expression.collections import seq
from expression.core import MailboxProcessor, Result, TailCall, aiotools, pipe, recursive_async, snd
from expression.system import CancellationTokenSource

from .combine import with_latest_from
from .create import interval
from .notification import Notification, OnCompleted, OnError, OnNext
from .observables import AsyncAnonymousObservable
from .observers import AsyncNotificationObserver, auto_detach_observer
from .transform import map
from .types import AsyncDisposable, AsyncObservable, AsyncObserver, Stream

TSource = TypeVar("TSource")
log = logging.getLogger(__name__)


def delay(seconds: float) -> Stream[TSource, TSource]:
    """Delay observable.

    Time shifts the observable sequence by the given timeout. The
    relative time intervals between the values are preserved.

    Args:
        seconds (float): Number of seconds to delay.

    Returns:
        Delayed stream.
    """

    def _delay(source: AsyncObservable[TSource]) -> AsyncObservable[TSource]:
        cts = CancellationTokenSource()

        async def subscribe_async(aobv: AsyncObserver[TSource]) -> AsyncDisposable:
            async def worker(inbox: MailboxProcessor[Tuple[Notification[TSource], datetime]]) -> None:
                @recursive_async
                async def loop() -> Result[None, Exception]:
                    ns, due_time = await inbox.receive()

                    diff = due_time - datetime.utcnow()
                    seconds = diff.total_seconds()
                    if seconds > 0:
                        await asyncio.sleep(seconds)

                    async def matcher() -> None:
                        with ns.match() as m:
                            for x in m.case(OnNext):
                                await aobv.asend(x)
                                return
                            for err in m.case(OnError):
                                await aobv.athrow(err)
                                return
                            while m.case(OnCompleted):
                                await aobv.aclose()
                                return

                    await matcher()
                    return TailCall()

                await loop()

            agent = MailboxProcessor.start(worker, cts.token)

            async def fn(ns: Notification[TSource]) -> None:
                due_time = datetime.utcnow() + timedelta(seconds=seconds)
                agent.post((ns, due_time))

            obv: AsyncNotificationObserver[TSource] = AsyncNotificationObserver(fn)
            subscription = await pipe(obv, source.subscribe_async)

            async def cancel() -> None:
                cts.cancel()
                await subscription.dispose_async()

            return AsyncDisposable.create(cancel)

        return AsyncAnonymousObservable(subscribe_async)

    return _delay


def debounce(seconds: float) -> Stream[TSource, TSource]:
    """Debounce observable stream.

    Ignores values from an observable sequence which are followed by
    another value before the given timeout.

    Args:
        seconds (float): Number of seconds to debounce.

    Returns:
        The debounced stream.
    """

    def _debounce(source: AsyncObservable[TSource]) -> AsyncObservable[TSource]:
        async def subscribe_async(aobv: AsyncObserver[TSource]) -> AsyncDisposable:
            safe_obv, auto_detach = auto_detach_observer(aobv)
            infinite: Iterable[int] = seq.infinite()

            async def worker(inbox: MailboxProcessor[Tuple[Notification[TSource], int]]) -> None:
                @recursive_async
                async def message_loop(current_index: int) -> Result[TSource, Exception]:
                    n, index = await inbox.receive()

                    with n.match() as m:
                        log.debug("debounce: %s, %d, %d", n, index, current_index)
                        for x in m.case(OnNext):
                            if index == current_index:
                                await safe_obv.asend(x)
                                current_index = index
                            elif index > current_index:
                                current_index = index

                        for err in m.case(OnError):
                            await safe_obv.athrow(err)

                        while m.case(OnCompleted):
                            await safe_obv.aclose()

                    return TailCall(current_index)

                await message_loop(-1)

            agent = MailboxProcessor.start(worker)

            indexer = iter(infinite)

            async def obv(n: Notification[TSource]) -> None:
                index = next(indexer)
                agent.post((n, index))

                async def worker() -> None:
                    log.debug("debounce, sleeping: %s", seconds)
                    await asyncio.sleep(seconds)
                    agent.post((n, index))

                aiotools.start(worker())

            obv_: AsyncObserver[TSource] = AsyncNotificationObserver(obv)
            dispose = await pipe(obv_, source.subscribe_async, auto_detach)

            async def cancel() -> None:
                await dispose.dispose_async()
                agent.post((OnCompleted, 0))

            return AsyncDisposable.create(cancel)

        return AsyncAnonymousObservable(subscribe_async)

    return _debounce


def sample(seconds: float) -> Stream[TSource, TSource]:
    def _sample(source: AsyncObservable[TSource]) -> AsyncObservable[TSource]:
        timer = interval(seconds, seconds)

        if seconds > 0:
            return pipe(source, with_latest_from(timer), map(snd))
        else:
            return source

    return _sample
