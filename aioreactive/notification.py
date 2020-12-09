from abc import ABC, abstractmethod
from enum import Enum
from typing import Any, Awaitable, Callable, Generic, Iterable, TypeVar, get_origin

from expression.core import SupportsMatch

from .types import AsyncObserver

TSource = TypeVar("TSource")
TMessage = TypeVar("TMessage")


class MsgKind(Enum):
    ON_NEXT = 1
    ON_ERROR = 2
    ON_COMPLETED = 3


class Notification(Generic[TSource], ABC):
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

    def __repr__(self) -> str:
        return str(self)


class OnNext(Notification[TSource], SupportsMatch[TSource]):
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

    def __match__(self, pattern: Any) -> Iterable[TSource]:
        origin: Any = get_origin(pattern)
        try:
            if isinstance(self, origin or pattern):
                return [self.value]
        except TypeError:
            pass
        return []

    def __eq__(self, other: Any) -> bool:
        if isinstance(other, OnNext):
            return self.value == other.value  # type: ignore
        return False

    def __str__(self) -> str:
        return f"OnNext({self.value})"


class OnError(Notification[TSource], SupportsMatch[Exception]):
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

    def __match__(self, pattern: Any) -> Iterable[Exception]:
        origin: Any = get_origin(pattern)
        try:
            if isinstance(self, origin or pattern):
                return [self.exception]
        except TypeError:
            pass
        return []

    def __eq__(self, other: Any) -> bool:
        if isinstance(other, OnError):
            return self.exception == other.exception
        return False

    def __str__(self) -> str:
        return f"OnError({self.exception})"


class _OnCompleted(Notification[TSource], SupportsMatch[bool]):
    """Represents an OnCompleted notification to an observer.

    Note: Do not use. Use the singleton `OnCompleted` instance instead.
    """

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

    def __match__(self, pattern: Any) -> Iterable[bool]:
        if self is pattern:
            return [True]

        origin: Any = get_origin(pattern)
        try:
            if isinstance(self, origin or pattern):
                return [True]
        except TypeError:
            pass
        return []

    def __eq__(self, other: Any) -> bool:
        if isinstance(other, _OnCompleted):
            return True
        return False

    def __str__(self) -> str:
        return "OnCompleted"


OnCompleted: _OnCompleted[Any] = _OnCompleted()
"""OnCompleted singleton instance."""
