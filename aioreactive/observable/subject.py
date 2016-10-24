from aioreactive.core.stream import AsyncStream

from .observable import Observable
from .observer import Observer


class Subject(Observable, Observer):

    def __init__(self):
        self._stream = AsyncStream()
        super().__init__(self._stream)

    async def on_next(self, value):
        await self._stream.asend(value)

    async def on_error(self, err):
        await self._stream.athrow(err)

    async def on_completed(self):
        await self._stream.aclose()
