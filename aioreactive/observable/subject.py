from aioreactive.core.stream import Stream

from .observable import Observable
from .observer import Observer


class Subject(Observable, Observer):
    def __init__(self):
        self._stream = Stream()
        super().__init__(self._stream)

    async def on_next(self, value):
        await self._stream.send(value)

    async def on_error(self, err):
        await self._stream.throw(err)

    async def on_completed(self):
        await self._stream.close()
