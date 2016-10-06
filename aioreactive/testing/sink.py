import asyncio
from typing import TypeVar

from aioreactive.abc import AsyncSink
from aioreactive.core.utils import anoop

T = TypeVar('T')


class Listener(AsyncSink):
    """A test listener.

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

    def __init__(self, send=anoop, throw=anoop, close=anoop):
        super().__init__()
        self._loop = asyncio.get_event_loop()
        self._values = []

        self._send = send
        self._throw = throw
        self._close = close

    async def send(self, value: T):
        time = self._loop.time()
        self._values.append((time, value))

        await self._send(value)

    async def throw(self, err: Exception):
        time = self._loop.time()
        self._values.append((time, err))

        await self._throw(err)

    async def close(self):
        time = self._loop.time()
        self._values.append((time,))

        await self._close()

    @property
    def values(self):
        return self._values
