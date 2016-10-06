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

    async def send_at(self, when: float, value: T):
        send = super().send

        async def task():
            await send(value)

        def callback():
            asyncio.ensure_future(task())

        self._loop.call_at(when, callback)

    async def send_later(self, delay: float, value: T):
        await asyncio.sleep(delay)
        await self.send(value)

    async def send_later_scheduled(self, delay: float, value: T):
        send = super().send

        async def task():
            await asyncio.sleep(delay)
            await send(value)
        asyncio.ensure_future(task())

    async def throw_at(self, when: float, err: Exception):
        async def task():
            await self.throw(err)

        def callback():
            asyncio.ensure_future(task())

        self._loop.call_at(when, callback)

    async def throw_later(self, delay: float, err: Exception):
        await asyncio.sleep(delay)
        await self.throw(err)

    async def throw_later_scheduled(self, delay: float, err: Exception):
        throw = super().throw

        async def task():
            await asyncio.sleep(delay)
            await throw(err)
        asyncio.ensure_future(task())

    async def close_at(self, when: float):
        async def task():
            await self.close()

        def callback():
            asyncio.ensure_future(task())

        self._loop.call_at(when, callback)

    async def close_later(self, delay: float):
        await asyncio.sleep(delay)
        await self.close()

    async def close_later_scheduled(self, delay: float):
        close = super().close

        async def task():
            await asyncio.sleep(delay)
            await close()
        asyncio.ensure_future(task())
