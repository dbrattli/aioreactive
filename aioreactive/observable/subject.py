from aioreactive.core.stream import AsyncStream

from .observable import AsyncObservable
from .observer import AsyncObserver


class AsyncSubject(AsyncObservable, AsyncObserver):

    def __init__(self):
        self._stream = AsyncStream()
        super().__init__(self._stream)

    async def on_next(self, value):
        await self._stream.asend(value)

    async def on_error(self, err):
        await self._stream.athrow(err)

    async def on_completed(self):
        await self._stream.aclose()
