from abc import ABCMeta, abstractmethod


class Cancellable(metaclass=ABCMeta):
    """A cancellable class with a context manager.

    Must implement the cancel method. Will cancel on exit."""

    @abstractmethod
    def cancel():
        return NotImplemented

    def __enter__(self):
        """Enter context management."""
        return self

    def __exit__(self, type, value, traceback) -> None:
        """Exit context management."""
        self.cancel()


class AsyncCancellable(metaclass=ABCMeta):
    """A cancellable class with a context manager.

    Must implement the cancel method. Will cancel on exit."""

    @abstractmethod
    async def acancel():
        return NotImplemented

    async def __aenter__(self):
        """Enter context management."""
        return self

    async def __aexit__(self, type, value, traceback) -> None:
        """Exit context management."""
        await self.acancel()
