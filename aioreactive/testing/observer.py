import logging
from typing import Awaitable, Callable, List, Tuple, TypeVar

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
    ):
        super().__init__(asend, athrow, aclose)

        self._values: List[Tuple[float, Notification[TSource]]] = []

        self._send = asend
        self._throw = athrow
        self._close = aclose

    def time(self):
        return self._loop.time()

    async def asend(self, value: TSource):
        log.debug("AsyncAnonymousObserver:asend(%s)", value)
        time = self.time()
        self._values.append((time, OnNext(value)))

        await self._send(value)
        await super().asend(value)

    async def athrow(self, error: Exception):
        log.debug("AsyncAnonymousObserver:athrow(%s)", error)
        time = self.time()
        self._values.append((time, OnError(error)))

        await self._throw(error)
        await super().athrow(error)

    async def aclose(self):
        log.debug("AsyncAnonymousObserver:aclose()")

        time = self.time()
        self._values.append((time, OnCompleted))

        await self._close()
        await super().aclose()

    @property
    def values(self) -> List[Tuple[float, Notification[TSource]]]:
        return self._values
