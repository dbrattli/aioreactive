import asyncio
from typing import TypeVar

from aioreactive import core

T = TypeVar('T')


class Stream(core.Stream):
    """A stream for testing.

    Provides methods for sending, throwing, and closing at a later
    time both relative and absolute.
    """

    def __init__(self):
        super().__init__()
        self._loop = asyncio.get_event_loop()

    async def asend_at(self, when: float, value: T):
        asend = super().asend

        async def task():
            await asend(value)

        def callback():
            asyncio.ensure_future(task())

        self._loop.call_at(when, callback)

    async def asend_later(self, delay: float, value: T):
        await asyncio.sleep(delay)
        await self.asend(value)

    async def asend_later_scheduled(self, delay: float, value: T):
        asend = super().asend

        async def task():
            await asyncio.sleep(delay)
            await asend(value)
        asyncio.ensure_future(task())

    async def athrow_at(self, when: float, err: Exception):
        async def task():
            await self.athrow(err)

        def callback():
            asyncio.ensure_future(task())

        self._loop.call_at(when, callback)

    async def athrow_later(self, delay: float, err: Exception):
        await asyncio.sleep(delay)
        await self.athrow(err)

    async def athrow_later_scheduled(self, delay: float, err: Exception):
        athrow = super().athrow

        async def task():
            await asyncio.sleep(delay)
            await athrow(err)
        asyncio.ensure_future(task())

    async def aclose_at(self, when: float):
        async def task():
            await self.aclose()

        def callback():
            asyncio.ensure_future(task())

        self._loop.call_at(when, callback)

    async def aclose_later(self, delay: float):
        await asyncio.sleep(delay)
        await self.aclose()

    async def close_later_scheduled(self, delay: float):
        aclose = super().aclose

        async def task():
            await asyncio.sleep(delay)
            await aclose()
        asyncio.ensure_future(task())
