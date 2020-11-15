from abc import ABC, abstractmethod
from enum import Enum
from typing import Any, Awaitable, Callable, Generic, Iterable, Optional, Type, TypeVar, overload

from expression.core import Matcher

from .types import AsyncObserver

TSource = TypeVar("TSource")
TMessage = TypeVar("TMessage")


class MsgKind(Enum):
    ON_NEXT = 1
    ON_ERROR = 2
    ON_COMPLETED = 3


class Case(Generic[TSource]):
    """Contains overloads to avoid type casting when pattern matching on
    the message (`Msg`) class

    Currently we wrap instead of inherit to make type checkers happy.
    """

    def __init__(self, match: Matcher[TSource]) -> None:
        self.match = match

    @overload
    def case(self, pattern: "Type[OnNext[TSource]]") -> Iterable[TSource]:
        ...

    @overload
    def case(self, pattern: "Type[OnError[TSource]]") -> Iterable[Exception]:
        ...

    @overload
    def case(self, pattern: "Type[OnCompleted_[TSource]]") -> Iterable[None]:
        ...

    def case(self, pattern: Any):
        return self.match.case(pattern)


class Notification(ABC, Generic[TSource]):
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

    @overload
    def match(self) -> "Case[TSource]":
        ...

    @overload
    def match(self, pattern: "Type[OnNext[TSource]]") -> Iterable[TSource]:
        ...

    @overload
    def match(self, pattern: "Type[OnError[TSource]]") -> Iterable[Exception]:
        ...

    @overload
    def match(self, pattern: "Type[OnCompleted_[TSource]]") -> Iterable[None]:
        ...

    def match(self, pattern: Optional[Any] = None) -> Any:
        m: Matcher[Any] = Matcher(self)
        return m.case(pattern) if pattern else Case(m)

    def __repr__(self) -> str:
        return str(self)


class OnNext(Notification[TSource]):
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
        if isinstance(self, pattern):
            return [self.value]
        return []

    def __eq__(self, other: Any) -> bool:
        if isinstance(other, OnNext):
            return self.value == other.value  # type: ignore
        return False

    def __str__(self) -> str:
        return f"OnNext({self.value})"


class OnError(Notification[TSource]):
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

    def __match__(self, pattern: Any) -> Iterable[TSource]:
        if isinstance(self, pattern):
            return [self.exception]
        return []

    def __eq__(self, other: Any) -> bool:
        if isinstance(other, OnError):
            return self.exception == other.exception
        return False

    def __str__(self) -> str:
        return f"OnError({self.exception})"


class OnCompleted_(Notification[TSource]):
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

    def __eq__(self, other: Any) -> bool:
        if isinstance(other, OnCompleted_):
            return True
        return False

    def __str__(self) -> str:
        return "OnCompleted"


OnCompleted: Notification[Any] = OnCompleted_()
"""OnCompleted singleton instance."""
