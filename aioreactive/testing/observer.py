import logging
from collections.abc import Awaitable, Callable
from typing import TypeVar

from aioreactive import AsyncAwaitableObserver
from aioreactive.notification import Notification, OnCompleted, OnError, OnNext
from aioreactive.utils import anoop


log = logging.getLogger(__name__)


TSource = TypeVar("TSource")


class AsyncTestObserver(AsyncAwaitableObserver[TSource]):
    """A recording AsyncAnonymousObserver.

    Records all values and events that happens and makes them available
    through the values property:

    The values are recorded as tuples:
        - sends: (time, T)
        - throws: (time, err)
        - close: (time,)

    Note: time is in integer milliseconds to avoid any rounding errors.
    """

    def __init__(
        self,
        asend: Callable[[TSource], Awaitable[None]] = anoop,
        athrow: Callable[[Exception], Awaitable[None]] = anoop,
        aclose: Callable[[], Awaitable[None]] = anoop,
    ) -> None:
        super().__init__(asend, athrow, aclose)

        self._values: list[tuple[float, Notification[TSource]]] = []

        self._send = asend
        self._throw = athrow
        self._close = aclose

    def time(self) -> float:
        return self._loop.time()

    async def asend(self, value: TSource) -> None:
        log.debug("AsyncAnonymousObserver:asend(%s)", value)
        time = self.time()
        self._values.append((time, OnNext(value)))

        await self._send(value)
        await super().asend(value)

    async def athrow(self, error: Exception) -> None:
        log.debug("AsyncAnonymousObserver:athrow(%s)", error)
        time = self.time()
        self._values.append((time, OnError(error)))

        await self._throw(error)
        await super().athrow(error)

    async def aclose(self) -> None:
        log.debug("AsyncAnonymousObserver:aclose()")

        time = self.time()
        self._values.append((time, OnCompleted()))

        await self._close()
        await super().aclose()

    @property
    def values(self) -> list[tuple[float, Notification[TSource]]]:
        return self._values
