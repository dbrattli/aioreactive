import asyncio
from typing import Awaitable, Callable, TypeVar

from aioreactive.types import AsyncObserver
from aioreactive.utils import anoop

TSource = TypeVar("TSource")


class AsyncTestObserver(AsyncObserver[TSource]):
    """A recording AsyncAnonymousObserver.

    Records all values and events that happens and makes them available
    through the values property:

    The values are recorded as tuples:
        - sends: (time, T)
        - throws: (time, err)
        - close: (time,)

    Note: we will not see the difference between sent and thrown
    exceptions. This should however not be any problem, and we have
    decided to keep it this way for simplicity.
    """

    def __init__(
        self,
        asend: Callable[[TSource], Awaitable[None]] = anoop,
        athrow: Callable[[Exception], Awaitable[None]] = anoop,
        aclose: Callable[[], Awaitable[None]] = anoop,
    ):
        super().__init__()
        self._values = []

        self._send = asend
        self._throw = athrow
        self._close = aclose

        self._loop = asyncio.get_event_loop()

    async def asend_core(self, value: TSource):
        print("AsyncAnonymousObserver:asend_core(%s)" % value)
        time = self._loop.time()
        self._values.append((time, value))

        await self._send(value)

    async def athrow_core(self, error: Exception):
        time = self._loop.time()
        self._values.append((time, error))

        await self._throw(error)

    async def aclose_core(self):
        time = self._loop.time()
        self._values.append((time,))

        await self._close()

    @property
    def values(self):
        return self._values
