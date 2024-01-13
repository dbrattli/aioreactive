import asyncio
from asyncio import Task
from typing import Any, TypeVar

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
        self._running_tasks: set[Task[Any]] = set()

    async def asend_at(self, when: float, value: TSource) -> None:
        task: Task[Any] | None = None

        async def worker() -> None:
            await self.asend(value)
            if task:
                self._running_tasks.remove(task)

        def callback() -> None:
            nonlocal task
            task = asyncio.ensure_future(worker())
            self._running_tasks.add(task)

        self._loop.call_at(when, callback)

    async def asend_later(self, delay: float, value: TSource) -> None:
        await asyncio.sleep(delay)
        await self.asend(value)

    async def asend_later_scheduled(self, delay: float, value: TSource) -> None:
        task: Task[Any] | None = None

        async def worker() -> None:
            await asyncio.sleep(delay)
            await self.asend(value)
            if task:
                self._running_tasks.remove(task)

        task = asyncio.ensure_future(worker())
        self._running_tasks.add(task)

    async def athrow_at(self, when: float, err: Exception) -> None:
        task: Task[Any] | None = None

        async def worker() -> None:
            await self.athrow(err)
            if task:
                self._running_tasks.remove(task)

        def callback() -> None:
            nonlocal task
            task = asyncio.ensure_future(worker())
            self._running_tasks.add(task)

        self._loop.call_at(when, callback)

    async def athrow_later(self, delay: float, err: Exception) -> None:
        await asyncio.sleep(delay)
        await self.athrow(err)

    async def athrow_later_scheduled(self, delay: float, err: Exception) -> None:
        task: Task[Any] | None = None

        async def worker() -> None:
            nonlocal task
            await asyncio.sleep(delay)
            await self.athrow(err)
            if task:
                self._running_tasks.remove(task)

        task = asyncio.ensure_future(worker())
        self._running_tasks.add(task)

    async def aclose_at(self, when: float) -> None:
        task: Task[Any] | None = None

        async def worker() -> None:
            await self.aclose()
            if task:
                self._running_tasks.remove(task)

        def callback() -> None:
            task = asyncio.ensure_future(worker())
            self._running_tasks.add(task)

        self._loop.call_at(when, callback)

    async def aclose_later(self, delay: float) -> None:
        await asyncio.sleep(delay)
        await self.aclose()

    async def close_later_scheduled(self, delay: float) -> None:
        task: Task[Any] | None = None

        async def worker() -> None:
            await asyncio.sleep(delay)
            await self.aclose()
            if task:
                self._running_tasks.remove(task)

        task = asyncio.ensure_future(worker())
        self._running_tasks.add(task)


class AsyncTestSubject(AsyncSubject[TSource], AsyncSubjectBase[TSource]):
    pass


class AsyncTestSingleSubject(AsyncSingleSubject[TSource], AsyncSubjectBase[TSource]):
    def __init__(self) -> None:
        super().__init__()


__all__ = ["AsyncTestSubject", "AsyncTestSingleSubject"]
