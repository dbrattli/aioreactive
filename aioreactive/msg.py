"""Internal messages used by mailbox processors. Do not import or use.
"""
from abc import ABC
from dataclasses import dataclass
from typing import Any, Iterable, NewType, TypeVar, get_origin

from expression.core import SupportsMatch
from expression.system import AsyncDisposable

from .notification import Notification
from .types import AsyncObservable

TSource = TypeVar("TSource")
TOther = TypeVar("TOther")

Key = NewType("Key", int)


class Msg(SupportsMatch[TSource], ABC):
    """Message base class."""


@dataclass
class SourceMsg(Msg[Notification[TSource]], SupportsMatch[TSource]):
    value: Notification[TSource]

    def __match__(self, pattern: Any) -> Iterable[Notification[TSource]]:
        origin: Any = get_origin(pattern)
        try:
            if isinstance(self, origin or pattern):
                return [self.value]
        except TypeError:
            pass
        return []


@dataclass
class OtherMsg(Msg[Notification[TOther]], SupportsMatch[TOther]):
    value: Notification[TOther]

    def __match__(self, pattern: Any) -> Iterable[Notification[TOther]]:
        origin: Any = get_origin(pattern)
        try:
            if isinstance(self, origin or pattern):
                return [self.value]
        except TypeError:
            pass
        return []


@dataclass
class DisposableMsg(Msg[AsyncDisposable], SupportsMatch[AsyncDisposable]):
    """Message containing a diposable."""

    disposable: AsyncDisposable

    def __match__(self, pattern: Any) -> Iterable[AsyncDisposable]:
        try:
            if isinstance(self, pattern):
                return [self.disposable]
        except TypeError:
            pass
        return []


@dataclass
class InnerObservableMsg(Msg[AsyncObservable[TSource]], SupportsMatch[AsyncObservable[TSource]]):
    """Message containing an inner observable."""

    inner_observable: AsyncObservable[TSource]

    def __match__(self, pattern: Any) -> Iterable[AsyncObservable[TSource]]:
        origin: Any = get_origin(pattern)
        try:
            if isinstance(self, origin or pattern):
                return [self.inner_observable]
        except TypeError:
            pass
        return []


@dataclass
class InnerCompletedMsg(Msg[TSource]):
    """Message notifying that the inner observable completed."""

    key: Key

    def __match__(self, pattern: Any) -> Iterable[Key]:
        origin: Any = get_origin(pattern)
        try:
            if isinstance(self, origin or pattern):
                return [self.key]
        except TypeError:
            pass
        return []


class CompletedMsg_(Msg[Any]):
    """Message notifying that the observable sequence completed."""

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


CompletedMsg = CompletedMsg_()  # Singleton


class DisposeMsg_(Msg[None]):
    """Message notifying that the operator got disposed."""

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


DisposeMsg = DisposeMsg_()  # Singleton


__all__ = ["Msg", "DisposeMsg", "CompletedMsg", "InnerCompletedMsg", "InnerObservableMsg", "DisposableMsg"]
