from asyncio import iscoroutinefunction

from aioreactive import abc


class AsyncDisposable(abc.AsyncDisposable):

    def __init__(self, dispose):
        assert iscoroutinefunction(dispose)
        self._dispose = dispose

    async def adispose(self):
        await self._dispose()


class AsyncCompositeDisposable(abc.AsyncDisposable):

    def __init__(self, *disposables):
        self._disposables = disposables

    async def adispose(self):
        for disposable in self._disposables:
            await disposable.adispose()
