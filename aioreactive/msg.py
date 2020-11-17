"""Internal messages used by mailbox processors. Do not import or use.
"""
from dataclasses import dataclass
from typing import Any, Generic, Iterable, Optional, Type, TypeVar, overload

from expression.core import Matcher
from expression.system import AsyncDisposable

from .notification import Notification
from .types import AsyncObservable

TSource = TypeVar("TSource")
TOther = TypeVar("TOther")


class Case(Generic[TSource]):
    """Contains overloads to avoid type casting when pattern matching on
    the message (`Msg`) class

    Currently we wrap instead of inherit to make type checkers happy.
    """

    def __init__(self, match: Matcher[TSource]) -> None:
        self.match = match

    @overload
    def case(self, pattern: "Type[InnerObservableMsg[TSource]]") -> Iterable[AsyncObservable[TSource]]:
        ...

    @overload
    def case(self, pattern: "Type[SourceMsg[TSource]]") -> Iterable[AsyncObservable[TSource]]:
        ...

    @overload
    def case(self, pattern: "Type[InnerCompletedMsg]") -> Iterable[int]:
        ...

    @overload
    def case(self, pattern: "Type[CompletedMsg]") -> "Iterable[CompletedMsg]":
        ...

    @overload
    def case(self, pattern: "Type[DisposeMsg]") -> "Iterable[DisposeMsg]":
        ...

    def case(self, pattern: Any):
        return self.match.case(pattern)


class Msg:
    """Message base class.

    Contains overloads for pattern matching to avoid any type casting
    later.
    """

    @overload
    def match(self) -> "Case[TSource]":
        ...

    @overload
    def match(self, pattern: "Type[DisposableMsg]") -> Iterable[AsyncDisposable]:
        ...

    @overload
    def match(self, pattern: "Type[SourceMsg[TSource]]") -> Iterable[Notification[TSource]]:
        ...

    @overload
    def match(self, pattern: "Type[OtherMsg[TSource]]") -> Iterable[Notification[TSource]]:
        ...

    @overload
    def match(self, pattern: "Type[InnerCompletedMsg]") -> Iterable[int]:
        ...

    @overload
    def match(self, pattern: "Type[CompletedMsg]") -> "Iterable[CompletedMsg]":
        ...

    @overload
    def match(self, pattern: "Type[DisposeMsg]") -> "Iterable[DisposeMsg]":
        ...

    @overload
    def match(self, pattern: "Type[InnerObservableMsg[TSource]]") -> Iterable[AsyncObservable[TSource]]:
        ...

    def match(self, pattern: Optional[Any] = None) -> Any:
        m: Matcher[Any] = Matcher(self)
        return m.case(pattern) if pattern else Case(m)


@dataclass
class SourceMsg(Msg, Generic[TSource]):
    value: Notification[TSource]

    def __match__(self, pattern: Any) -> Iterable[Notification[TSource]]:
        if isinstance(self, pattern):
            return [self.value]
        return []


@dataclass
class OtherMsg(Msg, Generic[TOther]):
    value: Notification[TOther]

    def __match__(self, pattern: Any) -> Iterable[Notification[TOther]]:
        if isinstance(self, pattern):
            return [self.value]
        return []


@dataclass
class DisposableMsg(Msg):
    """Message containing a diposable."""

    disposable: AsyncDisposable

    def __match__(self, pattern: Any) -> Iterable[AsyncDisposable]:
        if isinstance(self, pattern):
            return [self.disposable]
        return []


@dataclass
class InnerObservableMsg(Msg, Generic[TSource]):
    """Message containing an inner observable."""

    inner_observable: AsyncObservable[TSource]

    def __match__(self, pattern: Any) -> Iterable[AsyncObservable[TSource]]:
        if isinstance(self, pattern):
            return [self.inner_observable]
        return []


@dataclass
class InnerCompletedMsg(Msg):
    """Message notifying that the inner observable completed."""

    key: int

    def __match__(self, pattern: Any) -> Iterable[int]:
        if isinstance(self, pattern):
            return [self.key]
        return []


class CompletedMsg(Msg):
    """Message notifying that the observable sequence completed."""

    pass


CompletedMsg_ = CompletedMsg()  # Singleton


class DisposeMsg(Msg):
    """Message notifying that the operator got disposed."""

    pass


DisposeMsg_ = DisposeMsg()  # Singleton


__all__ = ["Msg", "DisposeMsg", "CompletedMsg", "InnerCompletedMsg", "InnerObservableMsg", "DisposableMsg"]
