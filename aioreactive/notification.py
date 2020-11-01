from abc import ABC, abstractmethod
from enum import Enum
from typing import Awaitable, Callable, TypeVar

from .types import AsyncObserver

TSource = TypeVar("TSource")
TMessage = TypeVar("TMessage")


class MsgKind(Enum):
    ON_NEXT = 1
    ON_ERROR = 2
    ON_COMPLETED = 3


class Notification(ABC):
    """Represents a message to a mailbox processor."""

    def __init__(self, kind: MsgKind):
        self.kind = kind  # Message kind

    @abstractmethod
    async def accept(
        self,
        asend: Callable[[TSource], Awaitable[None]],
        athrow: Callable[[Exception], Awaitable[None]],
        aclose: Callable[[], Awaitable[None]],
    ) -> None:
        raise NotImplementedError

    @abstractmethod
    async def accept_observer(self, obv: AsyncObserver[TSource]) -> None:
        raise NotImplementedError


class OnNext(Notification):
    """Represents an OnNext notification to an observer."""

    def __init__(self, value: TSource):
        """Constructs a notification of a new value."""
        super().__init__(MsgKind.ON_NEXT)
        self.value = value  # Message value

    async def accept(
        self,
        asend: Callable[[TSource], Awaitable[None]],
        athrow: Callable[[Exception], Awaitable[None]],
        aclose: Callable[[], Awaitable[None]],
    ) -> None:
        await asend(self.value)

    async def accept_observer(self, obv: AsyncObserver[TSource]) -> None:
        await obv.asend(self.value)

    def __str__(self) -> str:
        return f"OnNext({self.value})"


class OnError(Notification):
    """Represents an OnError notification to an observer."""

    def __init__(self, exception: Exception):
        """Constructs a notification of an exception."""
        super().__init__(MsgKind.ON_ERROR)
        self.exception = exception

    async def accept(
        self,
        asend: Callable[[TSource], Awaitable[None]],
        athrow: Callable[[Exception], Awaitable[None]],
        aclose: Callable[[], Awaitable[None]],
    ):
        await athrow(self.exception)

    async def accept_observer(self, obv: AsyncObserver[TSource]):
        await obv.athrow(self.exception)

    def __str__(self) -> str:
        return f"OnError({self.exception})"


class OnCompleted_(Notification):
    """Represents an OnCompleted notification to an observer."""

    def __init__(self):
        """Constructs a notification of the end of a sequence."""

        super().__init__(MsgKind.ON_COMPLETED)

    async def accept(
        self,
        asend: Callable[[TSource], Awaitable[None]],
        athrow: Callable[[Exception], Awaitable[None]],
        aclose: Callable[[], Awaitable[None]],
    ):
        await aclose()

    async def accept_observer(self, obv: AsyncObserver[TSource]):
        await obv.aclose()

    def __str__(self) -> str:
        return "OnCompleted"


OnCompleted = OnCompleted_()
"""OnCompleted singleton instance."""
