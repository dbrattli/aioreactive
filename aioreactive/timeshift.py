import asyncio
import logging
from collections.abc import Awaitable, Callable, Iterable
from datetime import datetime, timedelta, timezone
from typing import NoReturn, TypeVar

from expression import curry_flipped
from expression.collections import seq
from expression.core import (
    MailboxProcessor,
    TailCall,
    TailCallResult,
    aiotools,
    fst,
    pipe,
    tailrec_async,
)
from expression.system import CancellationTokenSource

from .combine import with_latest_from
from .create import interval
from .notification import Notification, OnCompleted, OnError, OnNext
from .observables import AsyncAnonymousObservable
from .observers import AsyncNotificationObserver, auto_detach_observer
from .transform import map
from .types import AsyncDisposable, AsyncObservable, AsyncObserver


_TSource = TypeVar("_TSource")
log = logging.getLogger(__name__)


@curry_flipped(1)
def delay(
    source: AsyncObservable[_TSource],
    seconds: float,
) -> AsyncObservable[_TSource]:
    """Delay observable.

    Time shifts the observable sequence by the given timeout. The
    relative time intervals between the values are preserved.

    Args:
        source: The source observable.
        seconds (float): Number of seconds to delay.

    Returns:
        Delayed stream.
    """
    cts = CancellationTokenSource()
    token = cts.token

    async def subscribe_async(aobv: AsyncObserver[_TSource]) -> AsyncDisposable:
        def worker(inbox: MailboxProcessor[tuple[Notification[_TSource], datetime]]) -> Awaitable[None]:
            @tailrec_async
            async def loop() -> TailCallResult[None, ...]:
                if token.is_cancellation_requested:
                    return

                ns, due_time = await inbox.receive()

                diff = due_time - datetime.now(timezone.utc)
                seconds = diff.total_seconds()
                if seconds > 0:
                    await asyncio.sleep(seconds)

                async def matcher() -> None:
                    match ns:
                        case OnNext(value=x):
                            await aobv.asend(x)
                            return
                        case OnError(exception=err):
                            await aobv.athrow(err)
                            return
                        case _:
                            await aobv.aclose()
                            return

                await matcher()
                return TailCall["..."]()

            return asyncio.ensure_future(loop())

        agent = MailboxProcessor.start(worker, token)

        async def fn(ns: Notification[_TSource]) -> None:
            due_time = datetime.now(timezone.utc) + timedelta(seconds=seconds)
            agent.post((ns, due_time))

        obv: AsyncNotificationObserver[_TSource] = AsyncNotificationObserver(fn)
        subscription = await source.subscribe_async(obv)

        async def cancel() -> None:
            log.debug("delay:cancel()")
            cts.cancel()
            await subscription.dispose_async()

        return AsyncDisposable.create(cancel)

    return AsyncAnonymousObservable(subscribe_async)


def debounce(
    seconds: float,
) -> Callable[[AsyncObservable[_TSource]], AsyncObservable[_TSource]]:
    def _debounce(source: AsyncObservable[_TSource]) -> AsyncObservable[_TSource]:
        async def subscribe_async(aobv: AsyncObserver[_TSource]) -> AsyncDisposable:
            safe_obv, auto_detach = auto_detach_observer(aobv)
            infinite: Iterable[int] = seq.infinite

            async def worker(inbox: MailboxProcessor[tuple[Notification[_TSource], int]]) -> None:
                @tailrec_async
                async def message_loop(
                    current_index: int,
                ) -> "TailCallResult[NoReturn, [int]]":
                    n, index = await inbox.receive()

                    match n:
                        case OnNext(value=x):
                            log.debug("debounce: %s, %d, %d", n, index, current_index)
                            if index == current_index:
                                await safe_obv.asend(x)
                                current_index = index
                            elif index > current_index:
                                current_index = index

                        case OnError(exception=err):
                            await safe_obv.athrow(err)

                        case _:
                            await safe_obv.aclose()

                    return TailCall[int](current_index)

                await message_loop(-1)

            agent = MailboxProcessor.start(worker)

            indexer = iter(infinite)

            async def obv(n: Notification[_TSource]) -> None:
                index = next(indexer)
                agent.post((n, index))

                async def worker() -> None:
                    log.debug("debounce, sleeping: %s", seconds)
                    await asyncio.sleep(seconds)
                    agent.post((n, index))

                aiotools.start(worker())

            obv_: AsyncObserver[_TSource] = AsyncNotificationObserver(obv)
            dispose = await pipe(obv_, source.subscribe_async, auto_detach)

            async def cancel() -> None:
                await dispose.dispose_async()
                agent.post((OnCompleted, 0))

            return AsyncDisposable.create(cancel)

        return AsyncAnonymousObservable(subscribe_async)

    return _debounce


def sample(
    seconds: float,
) -> Callable[[AsyncObservable[_TSource]], AsyncObservable[_TSource]]:
    def _sample(source: AsyncObservable[_TSource]) -> AsyncObservable[_TSource]:
        timer = interval(seconds, seconds)

        if seconds > 0:
            ret = pipe(
                source,
                with_latest_from(timer),
                map(fst),
            )
            return ret

        return source

    return _sample
