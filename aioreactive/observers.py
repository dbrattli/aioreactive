import logging
from asyncio import Future, iscoroutinefunction
from typing import AsyncIterable, AsyncIterator, Awaitable, Callable, List, Optional, Tuple, TypeVar

from fslash.core import MailboxProcessor
from fslash.system import AsyncDisposable, Disposable

from .notification import MsgKind, Notification, OnCompleted, OnError, OnNext
from .types import AsyncObserver
from .utils import anoop

log = logging.getLogger(__name__)

TSource = TypeVar("TSource")


class AsyncIteratorObserver(AsyncObserver[TSource], AsyncIterable[TSource]):
    """An async observer that might be iterated asynchronously."""

    def __init__(self) -> None:
        super().__init__()

        self._push: Future[TSource] = Future()
        self._pull: Future[TSource] = Future()

        self._awaiters: List[Future[TSource]] = []
        self._busy = False

    async def asend(self, value: TSource) -> None:
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
            fut: Future[TSource] = Future()
            self._awaiters.append(fut)
            await fut
            self._awaiters.remove(fut)

        self._busy = True

    async def wait_for_push(self) -> TSource:
        value = await self._push
        self._push = Future()
        self._pull.set_result(True)

        # Wake up any awaiters
        for awaiter in self._awaiters[:1]:
            awaiter.set_result(True)
        return value

    async def __aiter__(self) -> AsyncIterator[TSource]:
        log.debug("AsyncIteratorObserver:__aiter__")
        return self

    async def __anext__(self) -> TSource:
        log.debug("AsyncIteratorObserver:__anext__()")
        return await self.wait_for_push()


class AsyncAnonymousObserver(AsyncObserver[TSource]):
    """An anonymous AsyncObserver.

    Creates as sink where the implementation is provided by three
    optional and anonymous functions, asend, athrow and aclose. Used for
    listening to a source."""

    def __init__(
        self,
        asend: Callable[[TSource], Awaitable[None]] = anoop,
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

    async def asend(self, value: TSource) -> None:
        await self._asend(value)

    async def athrow(self, error: Exception) -> None:
        await self._athrow(error)

    async def aclose(self) -> None:
        await self._aclose()


def noop() -> AsyncObserver[TSource]:
    return AsyncAnonymousObserver(anoop, anoop, anoop)


def safe_observer(obv: AsyncObserver[TSource], disposable: AsyncDisposable) -> AsyncObserver[TSource]:
    """Safe observer that wraps the given observer. Makes sure that
    invocations are serialized and that the Rx grammar is not violated:

        `(OnNext*(OnError|OnCompleted)?)`

    I.e one or more OnNext, then terminates with a single OnError or
    OnCompleted.

    Args:
        obv: Observer to serialize access to
        disposable: Disposable to dispose when the observer closes.
    """

    async def worker(inbox: MailboxProcessor[Notification]):
        async def message_loop(stopped: bool) -> None:

            if stopped:
                return

            msg = await inbox.receive()
            if msg.kind == MsgKind.ON_NEXT:
                try:
                    await msg.accept_observer(obv)
                except Exception as ex:
                    await obv.athrow(ex)
                    stopped = True
            elif msg.kind == MsgKind.ON_ERROR:
                await disposable.dispose_async()
                await msg.accept_observer(obv)
                stopped = True
            else:
                await disposable.dispose_async()
                await obv.aclose()
                stopped = True

            return await message_loop(stopped)

        await message_loop(False)

    agent = MailboxProcessor.start(worker)

    async def asend(value: TSource) -> None:
        agent.post(OnNext(value))

    async def athrow(ex: Exception) -> None:
        agent.post(OnError(ex))

    async def aclose() -> None:
        agent.post(OnCompleted)

    return AsyncAnonymousObserver(asend, athrow, aclose)


class Msg:
    pass


class Disposable(Msg):
    def __init__(self, disposable: AsyncDisposable) -> None:
        self.disposable = disposable


class Dispose(Msg):
    pass


def auto_detach_observer(
    obv: AsyncObserver[TSource],
) -> Tuple[AsyncObserver[TSource], Callable[[Awaitable[AsyncDisposable]], Awaitable[AsyncDisposable]]]:
    async def worker(inbox: MailboxProcessor[Msg]):
        async def message_loop(disposables: List[AsyncDisposable]):
            cmd = await inbox.receive()
            if isinstance(cmd, Disposable):
                disposables.append(cmd.disposable)
            else:
                for disp in disposables:
                    await disp.dispose_async()
                return
            await message_loop(disposables)

        await message_loop([])

    agent = MailboxProcessor.start(worker)

    async def cancel():
        agent.post(Dispose)

    disp = AsyncDisposable.create(cancel)
    safe_obv = safe_observer(obv, disp)

    # Auto-detaches (disposes) the disposable when the observer completes with success or error.
    async def auto_detach(disposable: Awaitable[AsyncDisposable]):
        disp = await disposable
        agent.post(Disposable(disp))
        return disp

    return safe_obv, auto_detach


class AsyncAwaitableObserver(Future[TSource], AsyncObserver[TSource], Disposable):
    """An async observer abstract base class.

    Both a future and async observer. The future resolves with the last
    value before the observer is closed. A close without any values sent
    is the same as cancelling the future."""

    def __init__(
        self,
        asend: Callable[[TSource], Awaitable[None]] = anoop,
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

        self._has_value = False
        self._last_value: Optional[TSource] = None

        self._is_stopped = False

    async def asend(self, value: TSource) -> None:
        log.debug("AsyncAwaitableObserver:asend(%s)", str(value))

        if self._is_stopped:
            log.debug("Closed!!")
            return

        self._last_value = value
        self._has_value = True
        await self._asend(value)

    async def athrow(self, error: Exception) -> None:
        log.debug("AsyncAwaitableObserver:athrow()")
        if self._is_stopped:
            log.debug("Closed!!")
            return

        self._is_stopped = True

        self.set_exception(error)
        await self._athrow(error)

    async def aclose(self) -> None:
        log.debug("AsyncAwaitableObserver:aclose")

        if self._is_stopped:
            log.debug("Closed!!")
            return

        self._is_stopped = True

        if self._has_value:
            self.set_result(self._last_value)
        else:
            self.cancel()
        await self._aclose()

    def dispose(self) -> None:
        self._is_stopped = True
