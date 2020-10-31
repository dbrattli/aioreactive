import logging
from asyncio import Future, iscoroutinefunction
from typing import AsyncIterable, AsyncIterator, Awaitable, Callable, List, TypeVar

from aioreactive.core.types import AsyncObserver
from fslash.core import MailboxProcessor
from fslash.system import AsyncDisposable

from .bases import AsyncObserverBase
from .notification import MsgKind, Notification, OnCompleted, OnError, OnNext
from .utils import anoop

log = logging.getLogger(__name__)

TSource = TypeVar("TSource")
T = TypeVar("T")


class AsyncIteratorObserver(AsyncObserverBase[TSource], AsyncIterable[TSource]):
    """An async observer that might be iterated asynchronously."""

    def __init__(self) -> None:
        super().__init__()

        self._push: Future[TSource] = Future()
        self._pull: Future[TSource] = Future()

        self._awaiters: List[Future[TSource]] = []
        self._busy = False

    async def asend_core(self, value: TSource) -> None:
        log.debug("AsyncIteratorObserver:asend(%s)", value)

        await self._serialize_access()

        self._push.set_result(value)
        await self._wait_for_pull()

    async def athrow_core(self, error: Exception) -> None:
        print("AsyncIteratorObserver:athrow_core", error)
        await self._serialize_access()

        self._push.set_exception(error)
        await self._wait_for_pull()

    async def aclose_core(self) -> None:
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
        print("AsyncIteratorObserver:__aiter__")
        return self

    async def __anext__(self) -> TSource:
        print("AsyncIteratorObserver:__anext__")
        return await self.wait_for_push()


class AsyncAnonymousObserver(AsyncObserverBase[TSource]):
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
        print(asend)
        assert iscoroutinefunction(asend)
        self._send = asend

        assert iscoroutinefunction(athrow)
        self._throw = athrow

        assert iscoroutinefunction(aclose)
        self._close = aclose

    async def asend_core(self, value: TSource) -> None:
        await self._send(value)

    async def athrow_core(self, error: Exception) -> None:
        await self._throw(error)

    async def aclose_core(self) -> None:
        await self._close()


class AsyncNoopObserver(AsyncAnonymousObserver[TSource]):
    """An no operation Async Observer."""

    def __init__(
        self,
        asend: Callable[[TSource], Awaitable[None]] = anoop,
        athrow: Callable[[Exception], Awaitable[None]] = anoop,
        aclose: Callable[[], Awaitable[None]] = anoop,
    ) -> None:
        super().__init__(asend, athrow, aclose)


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
            msg = await inbox.receive()

            if stopped:
                return await message_loop(stopped)

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
