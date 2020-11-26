"""Internal messages used by mailbox processors. Do not import or use.
"""
from abc import abstractclassmethod
from dataclasses import dataclass
from typing import Any, Generic, Iterable, NewType, TypeVar

from expression.core import Matcher
from expression.system import AsyncDisposable

from .notification import Notification
from .types import AsyncObservable

TSource = TypeVar("TSource")
TOther = TypeVar("TOther")

Key = NewType("Key", int)


class Msg:
    """Message base class.

    Contains overloads for pattern matching to avoid any type casting
    later.
    """

    @abstractclassmethod
    def case(cls, matcher: Matcher) -> Any:
        raise NotImplementedError


@dataclass
class SourceMsg(Msg, Generic[TSource]):
    value: Notification[TSource]

    @classmethod
    def case(cls, matcher: Matcher) -> Iterable[Notification[TSource]]:
        """Helper to cast the match result to correct type."""
        return matcher.case(cls)

    def __match__(self, pattern: Any) -> Iterable[Notification[TSource]]:
        if isinstance(self, pattern):
            return [self.value]
        return []


@dataclass
class OtherMsg(Msg, Generic[TOther]):
    value: Notification[TOther]

    @classmethod
    def case(cls, matcher: Matcher) -> Iterable[Notification[TOther]]:
        """Helper to cast the match result to correct type."""

        return matcher.case(cls)

    def __match__(self, pattern: Any) -> Iterable[Notification[TOther]]:
        if isinstance(self, pattern):
            return [self.value]
        return []


@dataclass
class DisposableMsg(Msg):
    """Message containing a diposable."""

    disposable: AsyncDisposable

    @classmethod
    def case(cls, matcher: Matcher) -> Iterable[Notification[AsyncDisposable]]:
        """Helper to cast the match result to correct type."""

        return matcher.case(cls)

    def __match__(self, pattern: Any) -> Iterable[AsyncDisposable]:
        if isinstance(self, pattern):
            return [self.disposable]
        return []


@dataclass
class InnerObservableMsg(Msg, Generic[TSource]):
    """Message containing an inner observable."""

    inner_observable: AsyncObservable[TSource]

    @classmethod
    def case(cls, matcher: Matcher) -> Iterable[AsyncObservable[TSource]]:
        """Helper to cast the match result to correct type."""

        return matcher.case(cls)

    def __match__(self, pattern: Any) -> Iterable[AsyncObservable[TSource]]:
        if isinstance(self, pattern):
            return [self.inner_observable]
        return []


@dataclass
class InnerCompletedMsg(Msg):
    """Message notifying that the inner observable completed."""

    key: Key

    @classmethod
    def case(cls, matcher: Matcher) -> Iterable[Key]:
        """Helper to cast the match result to correct type."""

        return matcher.case(cls)

    def __match__(self, pattern: Any) -> Iterable[Key]:
        if isinstance(self, pattern):
            return [self.key]
        return []


class CompletedMsg(Msg):
    """Message notifying that the observable sequence completed."""

    @classmethod
    def case(cls, matcher: Matcher) -> Iterable[bool]:
        """Helper to cast the match result to correct type."""

        return matcher.case(cls)


CompletedMsg_ = CompletedMsg()  # Singleton


class DisposeMsg(Msg):
    """Message notifying that the operator got disposed."""

    pass


DisposeMsg_ = DisposeMsg()  # Singleton


__all__ = ["Msg", "DisposeMsg", "CompletedMsg", "InnerCompletedMsg", "InnerObservableMsg", "DisposableMsg"]
