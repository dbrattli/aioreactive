import asyncio
from typing import TypeVar

from aioreactive import AsyncObserver
from aioreactive.subject import AsyncSingleSubject, AsyncSubject


TSource = TypeVar("TSource")


class AsyncSubjectBase(AsyncObserver[TSource]):
    """A subject base for testing.

    Provides methods for sending, throwing, and closing at a later
    time both relative and absolute.
    """

    def __init__(self) -> None:
        self._loop = asyncio.get_event_loop()

    async def asend_at(self, when: float, value: TSource) -> None:
        async def task() -> None:
            await self.asend(value)

        def callback() -> None:
            asyncio.ensure_future(task())

        self._loop.call_at(when, callback)

    async def asend_later(self, delay: float, value: TSource) -> None:
        await asyncio.sleep(delay)
        await self.asend(value)

    async def asend_later_scheduled(self, delay: float, value: TSource) -> None:
        async def task() -> None:
            await asyncio.sleep(delay)
            await self.asend(value)

        asyncio.ensure_future(task())

    async def athrow_at(self, when: float, err: Exception) -> None:
        async def task() -> None:
            await self.athrow(err)

        def callback() -> None:
            asyncio.ensure_future(task())

        self._loop.call_at(when, callback)

    async def athrow_later(self, delay: float, err: Exception) -> None:
        await asyncio.sleep(delay)
        await self.athrow(err)

    async def athrow_later_scheduled(self, delay: float, err: Exception) -> None:
        async def task() -> None:
            await asyncio.sleep(delay)
            await self.athrow(err)

        asyncio.ensure_future(task())

    async def aclose_at(self, when: float) -> None:
        async def task() -> None:
            await self.aclose()

        def callback() -> None:
            asyncio.ensure_future(task())

        self._loop.call_at(when, callback)

    async def aclose_later(self, delay: float) -> None:
        await asyncio.sleep(delay)
        await self.aclose()

    async def close_later_scheduled(self, delay: float) -> None:
        async def task() -> None:
            await asyncio.sleep(delay)
            await self.aclose()

        asyncio.ensure_future(task())


class AsyncTestSubject(AsyncSubject[TSource], AsyncSubjectBase[TSource]):
    pass


class AsyncTestSingleSubject(AsyncSingleSubject[TSource], AsyncSubjectBase[TSource]):
    def __init__(self) -> None:
        super().__init__()


__all__ = ["AsyncTestSubject", "AsyncTestSingleSubject"]
