from abc import ABCMeta, abstractmethod


class Disposable(metaclass=ABCMeta):
    """A disposable class with a context manager.

    Must implement the cancel method. Will cancel on exit."""

    @abstractmethod
    def dispose(self):
        return NotImplemented

    def __enter__(self):
        """Enter context management."""
        return self

    def __exit__(self, type, value, traceback) -> None:
        """Exit context management."""
        self.dispose()


class AsyncDisposable(metaclass=ABCMeta):
    """A disposable class with a context manager.

    Must implement the cancel method. Will cancel on exit."""

    @abstractmethod
    async def adispose(self):
        return NotImplemented

    async def __aenter__(self):
        """Enter context management."""
        return self

    async def __aexit__(self, type, value, traceback) -> None:
        """Exit context management."""
        await self.adispose()
