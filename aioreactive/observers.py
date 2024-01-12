import logging
from asyncio import Future, iscoroutinefunction
from collections.abc import AsyncIterable, AsyncIterator, Awaitable, Callable, Coroutine
from typing import Any, TypeVar, cast

from expression.core import MailboxProcessor, TailCall, tailrec_async
from expression.system import AsyncDisposable, CancellationTokenSource, Disposable

from .msg import Msg
from .notification import MsgKind, Notification, OnCompleted, OnError, OnNext
from .types import AsyncObservable, AsyncObserver
from .utils import anoop


log = logging.getLogger(__name__)

_TSource = TypeVar("_TSource")


class AsyncIteratorObserver(AsyncObserver[_TSource], AsyncIterable[_TSource], AsyncDisposable):
    """An async observer that might be iterated asynchronously."""

    def __init__(self, source: AsyncObservable[_TSource]) -> None:
        super().__init__()

        self._push: Future[_TSource] = Future()
        self._pull: Future[bool] = Future()

        self._awaiters: list[Future[bool]] = []
        self._subscription: AsyncDisposable | None = None
        self._source = source
        self._busy = False

    async def asend(self, value: _TSource) -> None:
        log.debug("AsyncIteratorObserver:asend(%s)", value)

        await self._serialize_access()

        self._push.set_result(value)
        await self._wait_for_pull()

    async def athrow(self, error: Exception) -> None:
        log.debug("AsyncIteratorObserver:athrow()", error)
        await self._serialize_access()

        self._push.set_exception(error)
        await self._wait_for_pull()

    async def aclose(self) -> None:
        await self._serialize_access()

        self._push.set_exception(StopAsyncIteration)
        await self._wait_for_pull()

    async def _wait_for_pull(self) -> None:
        await self._pull
        self._pull = Future()
        self._busy = False

    async def _serialize_access(self) -> None:
        # Serialize producer event to the iterator
        while self._busy:
            fut: Future[bool] = Future()
            self._awaiters.append(fut)
            await fut
            self._awaiters.remove(fut)

        self._busy = True

    async def wait_for_push(self) -> _TSource:
        if self._subscription is None:
            self._subscription = await self._source.subscribe_async(self)

        value = await self._push
        self._push = Future()
        self._pull.set_result(True)

        # Wake up any awaiters
        for awaiter in self._awaiters[:1]:
            awaiter.set_result(True)
        return value

    async def dispose_async(self) -> None:
        if self._subscription is not None:
            await self._subscription.dispose_async()
        self._subscription = None

    def __aiter__(self) -> AsyncIterator[_TSource]:
        log.debug("AsyncIteratorObserver:__aiter__")
        return self

    async def __anext__(self) -> _TSource:
        log.debug("AsyncIteratorObserver:__anext__()")
        return await self.wait_for_push()


class AsyncAnonymousObserver(AsyncObserver[_TSource]):
    """An anonymous AsyncObserver.

    Creates as sink where the implementation is provided by three
    optional and anonymous functions, asend, athrow and aclose. Used for
    listening to a source.
    """

    def __init__(
        self,
        asend: Callable[[_TSource], Awaitable[None]] | None = None,
        athrow: Callable[[Exception], Awaitable[None]] | None = None,
        aclose: Callable[[], Awaitable[None]] | None = None,
    ) -> None:
        super().__init__()
        self._asend = asend or anoop
        assert iscoroutinefunction(self._asend)

        self._athrow = athrow or anoop
        assert iscoroutinefunction(self._athrow)

        self._aclose = aclose or anoop
        assert iscoroutinefunction(self._aclose)

    async def asend(self, value: _TSource) -> None:
        await self._asend(value)

    async def athrow(self, error: Exception) -> None:
        await self._athrow(error)

    async def aclose(self) -> None:
        await self._aclose()


class AsyncNotificationObserver(AsyncObserver[_TSource]):
    """Observer created from an async notification processing function."""

    def __init__(self, fn: Callable[[Notification[_TSource]], Awaitable[None]]) -> None:
        self._fn = fn

    async def asend(self, value: _TSource) -> None:
        await self._fn(OnNext(value))

    async def athrow(self, error: Exception) -> None:
        await self._fn(OnError(error))

    async def aclose(self) -> None:
        await self._fn(OnCompleted())


def noop() -> AsyncObserver[Any]:
    return AsyncAnonymousObserver(anoop, anoop, anoop)


def safe_observer(obv: AsyncObserver[_TSource], disposable: AsyncDisposable) -> AsyncObserver[_TSource]:
    """Safe observer that wraps the given observer.

    Makes sure that
    invocations are serialized and that the Rx grammar is not violated:

        `(OnNext*(OnError|OnCompleted)?)`

    I.e one or more OnNext, then terminates with a single OnError or
    OnCompleted.

    Args:
        obv: Observer to serialize access to
        disposable: Disposable to dispose when the observer closes.
    """

    async def worker(inbox: MailboxProcessor[Notification[_TSource]]) -> None:
        async def message_loop(running: bool) -> None:
            while running:
                msg = await inbox.receive()
                if msg.kind == MsgKind.ON_NEXT:
                    try:
                        await msg.accept_observer(obv)
                    except Exception as ex:
                        await obv.athrow(ex)
                        running = False
                elif msg.kind == MsgKind.ON_ERROR:
                    await disposable.dispose_async()
                    await msg.accept_observer(obv)
                    running = False
                else:
                    await disposable.dispose_async()
                    await obv.aclose()
                    running = False

        await message_loop(running=True)

    agent = MailboxProcessor.start(worker)

    async def asend(value: _TSource) -> None:
        agent.post(OnNext(value))

    async def athrow(ex: Exception) -> None:
        agent.post(OnError(ex))

    async def aclose() -> None:
        agent.post(OnCompleted())

    return AsyncAnonymousObserver(asend, athrow, aclose)


def auto_detach_observer(
    obv: AsyncObserver[_TSource],
) -> tuple[
    AsyncObserver[_TSource],
    Callable[[Coroutine[None, None, AsyncDisposable]], Coroutine[None, None, AsyncDisposable]],
]:
    cts = CancellationTokenSource()
    token = cts.token

    async def worker(inbox: MailboxProcessor[Msg[_TSource]]) -> None:
        @tailrec_async
        async def message_loop(
            disposables: list[AsyncDisposable],
        ) -> Any:
            if token.is_cancellation_requested:
                return

            cmd = await inbox.receive()
            match cmd:
                case Msg(tag="disposable", disposable=disposable):
                    disposables.append(disposable)
                case _:
                    for disp in disposables:
                        await disp.dispose_async()
                    return
            return TailCall[list[AsyncDisposable]](disposables)

        await message_loop([])

    agent = MailboxProcessor.start(worker, token)

    async def cancel() -> None:
        cts.cancel()
        agent.post(Msg(dispose=True))

    canceller = AsyncDisposable.create(cancel)
    safe_obv = safe_observer(obv, canceller)

    # Auto-detaches (disposes) the disposable when the observer completes with success or error.
    async def auto_detach(async_disposable: Coroutine[None, None, AsyncDisposable]) -> AsyncDisposable:
        disposable = await async_disposable
        agent.post(Msg(disposable=disposable))
        return disposable

    return safe_obv, auto_detach


class AsyncAwaitableObserver(Future[_TSource], AsyncObserver[_TSource], Disposable):
    """An async awaitable observer.

    Both a future and async observer. The future resolves with the last
    value before the observer is closed. A close without any values sent
    is the same as cancelling the future.
    """

    def __init__(
        self,
        asend: Callable[[_TSource], Awaitable[None]] = anoop,
        athrow: Callable[[Exception], Awaitable[None]] = anoop,
        aclose: Callable[[], Awaitable[None]] = anoop,
    ) -> None:
        super().__init__()

        assert iscoroutinefunction(asend)
        self._asend = asend

        assert iscoroutinefunction(athrow)
        self._athrow = athrow

        assert iscoroutinefunction(aclose)
        self._aclose = aclose

        self._last_value: _TSource = cast(_TSource, None)
        self._is_stopped = False
        self._has_value = False

    async def asend(self, value: _TSource) -> None:
        log.debug("AsyncAwaitableObserver:asend(%s)", str(value))

        if self._is_stopped:
            log.debug("AsyncAwaitableObserver:asend(), Closed!!")
            return

        self._last_value = value
        self._has_value = True
        await self._asend(value)

    async def athrow(self, error: Exception) -> None:
        log.debug("AsyncAwaitableObserver:athrow()")
        if self._is_stopped:
            log.debug("AsyncAwaitableObserver:athrow(), Closed!!")
            return

        self._is_stopped = True

        self.set_exception(error)
        await self._athrow(error)

    async def aclose(self) -> None:
        log.debug("AsyncAwaitableObserver:aclose")

        if self._is_stopped:
            log.debug("AsyncAwaitableObserver:aclose(), Closed!!")
            return

        self._is_stopped = True

        if self._has_value:
            self.set_result(self._last_value)
        else:
            self.cancel()
        await self._aclose()

    def dispose(self) -> None:
        log.debug("AsyncAwaitableObserver:dispose()")

        self._is_stopped = True
